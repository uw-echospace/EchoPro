import copy
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, Union

import pandas as pd

from . import live_data_loading as eldl, live_data_processing as eldp
from .live_acoustics import compute_nasc, format_acoustic_dataset, preprocess_acoustic_data
from .live_biology import (
    bin_length_data,
    compute_average_weights,
    compute_sigma_bs,
    length_bin_counts,
    length_bin_weights,
    length_weight_regression,
    number_proportions,
    preprocess_biology_data,
    weight_proportions,
)
from .live_core import LIVE_DATA_STRUCTURE
from .live_spatial_methods import initialize_grid
from .sql_methods import query_processed_files


class LiveSurvey:
    """
    A real-time processing version of the `echopop` base `Survey` class that ingests biological,
    acoustic, and event meta data to provide population estimates when generated.
    """

    def __init__(
        self,
        live_init_config_path: Union[str, Path],
        live_file_config_path: Union[str, Path],
        cloud_storage_options: dict = {},
        verbose: bool = True,
    ):
        # Initialize `meta` attribute
        self.meta = copy.deepcopy(LIVE_DATA_STRUCTURE["meta"])
        # ---- Add datetime
        self.meta["date"] = datetime.now()

        # Loading the configuration settings and definitions that are used to
        # initialize the Survey class object
        self.config = eldl.live_configuration(live_init_config_path, live_file_config_path)
        # ---- Initialize config key for database files
        self.config.update(
            {"database": {key: None for key in self.config["input_directories"].keys()}}
        )
        # ---- Add cloud storage options, if needed
        self.config.update({"storage_options": cloud_storage_options})

        # Initialize input attribute
        self.input = copy.deepcopy(LIVE_DATA_STRUCTURE["input"])

        # Initialize database attribute
        self.database = copy.deepcopy(LIVE_DATA_STRUCTURE["database"])

        # Initialize the results attribute
        self.results = copy.deepcopy(LIVE_DATA_STRUCTURE["results"])

        # Initialize the extrapolation grid
        initialize_grid(self.config)

        # Add database paths to configuration attribute
        eldp.configure_database_paths(self.config)

        # Configure the spatial settings
        self.input.update({"spatial": eldl.configure_spatial_settings(self.config)})

        # TODO: Add verbosity for printing database filepaths/connections
        if verbose:
            pass

    def __repr__(self):

        # Get any acoustic files created
        if "acoustic_files" in self.meta["provenance"]:
            # ---- Get the filenames
            acoustic_filenames = self.meta["provenance"]["acoustic_files_read"]
            # ---- Subset if many files are being processed
            if len(acoustic_filenames) > 2:
                acoustic_filenames = (
                    acoustic_filenames[:2] + ["..."] + [f"[n = {len(acoustic_filenames)}]"]
                )
            # ---- Format string
            acoustic_files = ", ".join(acoustic_filenames)
        else:
            acoustic_files = "None"

        # Get any biology files created
        if "biology_files" in self.meta["provenance"]:
            # ---- Get the filenames
            biology_filenames = self.meta["provenance"]["biology_files_read"]
            # ---- Subset if many files are being processed
            if len(biology_filenames) > 4:
                biology_filenames = biology_filenames + ["..."]
            # ---- Format string
            biology_files = ", ".join(biology_filenames)
        else:
            biology_files = "None"

        # Get linked database names
        linked_dbs = "\n   ".join(
            [f"{key.title()}: {db}" for key, db in self.config["database"].items()]
        )

        return (
            f"LiveSurvey-class object \n"
            f"Timestamp: {self.meta['date']} \n"
            f"Acoustic files being processed: \n   {acoustic_files}\n"
            f"Biology files being processed: \n   {biology_files}\n"
            f"Linked databases: \n   {linked_dbs}"
        )

    def __str__(self):
        return self.__repr__()

    def load_acoustic_data(
        self, xarray_kwargs: dict = {}, input_filenames: Optional[list] = None, verbose: bool = True
    ):

        # Validate the data directory and format the filepaths
        acoustic_files = eldl.validate_data_directory(
            self.config, dataset="acoustics", input_filenames=input_filenames
        )

        # Read in the acoustic data files
        if acoustic_files:
            # ! [REQUIRES DASK] ---- Read in the listed file
            # ---- Read in the acoustic data files
            prc_nasc_df, acoustic_data_units = eldl.read_acoustic_files(
                acoustic_files, xarray_kwargs=xarray_kwargs
            )
            # ---- Add the `acoustic_data_units` to the dictionary
            self.config["acoustics"]["dataset_units"] = acoustic_data_units
            # ---- Preprocess the acoustic dataset
            # TODO: SettingWithCopyWarning:
            self.input["acoustics"]["prc_nasc_df"] = preprocess_acoustic_data(
                prc_nasc_df.copy(), self.input["spatial"], self.config
            )
            # ---- Add meta key
            self.meta["provenance"].update(
                {
                    "acoustic_files_read": acoustic_files,
                }
            )
            # TODO: Add verbosity for printing database filepaths/connections
            if verbose:
                # ---- Create file list
                file_list = "\n".join(acoustic_files)
                print(f"The following acoustic files are being processed:\n" f"{file_list}.")
        else:
            self.input["acoustics"]["prc_nasc_df"] = None

    def load_biology_data(
        self, pandas_kwargs: dict = {}, input_filenames: Optional[list] = None, verbose: bool = True
    ):

        # Validate the data directory and format the filepaths
        biology_files = eldl.validate_data_directory(
            self.config, dataset="biology", input_filenames=input_filenames
        )

        # ! REMOVE
        self.meta["provenance"]["biology_files_checkpoint1"] = biology_files

        # TODO: Add verbosity for printing database filepaths/connections
        if biology_files and verbose:
            # ---- Create file list
            file_list = "\n".join(biology_files)
            print(f"The following biological files are being processed:\n" f"{file_list}.")

            # Read in the biology data files
            initial_biology_output = eldl.read_biology_files(
                biology_files, self.config, pandas_kwargs=pandas_kwargs
            )

            # ! REMOVE
            self.meta["provenance"]["biology_files_checkpoint2"] = {
                key: df.shape for key, df in initial_biology_output.items()
            }

            # Preprocess the biology dataset
            self.input["biology"], self.input["biology_processed"] = preprocess_biology_data(
                initial_biology_output, self.input["spatial"], self.config
            )

            # ! REMOVE
            self.meta["provenance"]["biology_files_checkpoint3"] = {
                key: df.shape for key, df in self.input["biology_processed"].items()
            }

            # Add meta key
            self.meta["provenance"].update(
                {
                    "biology_files_read": biology_files,
                }
            )

    def process_biology_data(self):

        # TODO: How and when should the already processed data be imported?
        # Separate out processed and unprocessed biological data
        # ----- Unprocessed
        biology_unprocessed = self.input["biology"]

        # Get database root directory
        root_directory = self.config["database_directory"]

        # Check if data are present
        unprocess_data_dfs = [
            True if isinstance(df, pd.DataFrame) and not df.empty else False
            for _, df in biology_unprocessed.items()
        ]
        # ---- Proceed in processing the unprocessed data
        if all(unprocess_data_dfs):

            # Compute `sigma_bs` by sending it to the appropriate database table
            compute_sigma_bs(
                biology_unprocessed["specimen_df"], biology_unprocessed["length_df"], self.config
            )

            # Bin the length measurements of the biological data
            bin_length_data(biology_unprocessed, self.config["length_distribution"])

            # Compute the length-weight regression and add it to the SQL table
            length_weight_df = length_weight_regression(
                biology_unprocessed["specimen_df"], self.config["length_distribution"], self.config
            )

            # Compute length-binned counts for the aggregated and individual-based measurements
            specimen_binned, specimen_binned_filtered, length_binned = length_bin_counts(
                biology_unprocessed["length_df"], biology_unprocessed["specimen_df"], self.config
            )

            # Compute the number proportions
            specimen_number_proportion, length_number_proportion, sex_number_proportions = (
                number_proportions(
                    specimen_binned, specimen_binned_filtered, length_binned, self.config
                )
            )

            # Compute the length-binned weights for the aggregated and individual-based measurements
            length_weight_binned, specimen_weight_binned = length_bin_weights(
                biology_unprocessed["length_df"],
                biology_unprocessed["specimen_df"],
                length_weight_df,
                self.config,
            )

            # Calculate the average weights among male, female, and all fish
            self.input["weight_stratum_df"] = compute_average_weights(
                specimen_number_proportion,
                length_number_proportion,
                sex_number_proportions,
                length_weight_df,
                self.config["length_distribution"],
                self.config,
            )

            # Compute the weight proportions
            self.input["biology"].update(
                {
                    "proportions": weight_proportions(
                        biology_unprocessed["catch_df"],
                        specimen_weight_binned,
                        length_weight_binned,
                        length_number_proportion,
                        length_weight_df,
                        self.config,
                    )
                }
            )

            # Update the database
            query_processed_files(
                root_directory,
                self.config["input_directories"]["biology"],
                self.meta["provenance"]["biology_files_read"],
                processed=True,
            )

            # Add meta key
            self.meta["provenance"].update(
                {"biology_files_processed": self.meta["provenance"]["biology_files_read"]}
            )

    def process_acoustic_data(self, echometrics: bool = True, verbose: bool = True):

        # Check for if any data is present; if not, provide report
        if self.input["acoustics"]["prc_nasc_df"] is None:
            # ---- Set the corresponding `nasc_df` DataFrame to None
            self.input["nasc_df"] = None
            # ---- Print, if verbose
            if verbose:
                print(
                    "No acoustic data located in `*.input['acoustics']['prc_nasc_df']"
                    " DataFrame. Data processing step will therefore be skipped."
                )
        else:
            # Get the unprocessed acoustic data
            acoustic_data_df = self.input["acoustics"]["prc_nasc_df"]

            # Integrate NASC (and compute the echometrics, if necessary)
            nasc_data_df = compute_nasc(acoustic_data_df, self.config, echometrics)

            # Format the dataframe and insert into the LiveSurvey object
            self.input["acoustics"]["nasc_df"] = format_acoustic_dataset(
                nasc_data_df, self.config, self.meta
            )

            # Add meta key
            self.meta["provenance"].update(
                {"acoustic_files_processed": self.meta["provenance"]["acoustic_files_read"]}
            )

    def estimate_population(
        self, working_dataset: Literal["acoustic", "biology"], verbose: bool = True
    ):

        self.meta["provenance"][f"{working_dataset}_population"] = False

        # method
        if working_dataset == "acoustic":
            eldp.acoustic_pipeline(
                self.input["acoustics"],
                self.input["spatial"]["strata"],
                self.config,
                verbose=verbose,
                contrast_columns=["ship_id"],
            )
            # --- Validate successful run
            self.meta["provenance"]["acoustic_population"] = True

        # method
        if working_dataset == "biology":
            eldp.biology_pipeline(
                self.input["biology"], self.input["spatial"]["strata"], self.config, verbose=verbose
            )
            # --- Validate successful run
            self.meta["provenance"]["biology_population"] = True
