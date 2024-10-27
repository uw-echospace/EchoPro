from typing import Optional, Union

import numpy as np
import pandas as pd

from ..acoustics import to_linear, ts_length_regression
from .live_spatial_methods import apply_griddify_definitions, apply_spatial_definitions
from .sql_methods import query_processed_files, sql_data_exchange


# TODO: Documentation
def configure_transmit_frequency(
    frequency_values: pd.Series, transmit_settings: dict, current_units: str
):

    # Extract transmit frequency units defined in configuration file
    configuration_units = transmit_settings["units"]

    # Transform the units, if necessary
    # ---- Hz to kHz
    if current_units == "Hz" and configuration_units == "kHz":
        return frequency_values * 1e-3
    # ---- kHz to Hz
    elif current_units == "kHz" and configuration_units == "Hz":
        return frequency_values * 1e3
    # ---- No change
    else:
        return frequency_values


# TODO: Documentation
def preprocess_acoustic_data(
    survey_data: pd.DataFrame, spatial_dict: dict, file_configuration: dict
) -> pd.DataFrame:

    # Get acoustic processing settings
    acoustic_analysis_settings = file_configuration["acoustics"]
    # ---- Extract the fined acoustic frequency
    transmit_settings = acoustic_analysis_settings["transmit"]

    # Filter the dataset
    # ---- Configure `frequency_nominal`, if necessary
    survey_data.loc[:, "frequency_nominal"] = configure_transmit_frequency(
        survey_data.loc[:, "frequency_nominal"],
        transmit_settings,
        acoustic_analysis_settings["dataset_units"]["frequency"],
    )
    # ---- Filter out any unused frequency coordinates
    prc_nasc_df_filtered = (
        survey_data[survey_data["frequency_nominal"] == transmit_settings["frequency"]]
        # ---- Drop NaN/NaT values from longitude/latitude/ping_time
        .dropna(subset=["longitude", "latitude", "ping_time"])
    )

    # Get grid coordinates
    prc_nasc_df_filtered = pd.concat(
        [
            prc_nasc_df_filtered,
            apply_griddify_definitions(prc_nasc_df_filtered, file_configuration["geospatial"]),
        ],
        axis=1,
    )

    # Apply spatial settings
    prc_nasc_df_filtered = prc_nasc_df_filtered.assign(
        stratum=apply_spatial_definitions(prc_nasc_df_filtered["latitude"], spatial_dict)
    )

    # Remaining adjustments to the acoustic data prior to being passed to the `LiveSurvey` object
    # ---- Add `ship_id` from the file configuration
    prc_nasc_df_filtered.loc[:, "ship_id"] = file_configuration["ship_id"]
    # ---- Replace NASC `NaN` values with `0.0`
    prc_nasc_df_filtered.loc[:, "NASC"] = prc_nasc_df_filtered.loc[:, "NASC"].fillna(0.0)
    # ---- Drop the `frequency_nominal` column and return the output
    return prc_nasc_df_filtered.drop(columns=["frequency_nominal"])


# TODO: Documentation
def average_sigma_bs(
    length: Union[pd.DataFrame, float, int], weights: Optional[Union[float, int, str]] = None
):

    # Function approach for dataframe input
    if isinstance(length, pd.DataFrame):
        if "length" not in length.columns:
            raise ValueError("Column [`length`] missing from dataframe input `length`.")
        elif "TS_L_slope" not in length.columns:
            raise ValueError("Column [`TS_L_slope`] missing from dataframe input `length`.")
        elif "TS_L_slope" not in length.columns:
            raise ValueError("Column [`TS_L_intercept`] missing from dataframe input `length`.")
        else:
            # ---- Compute the TS (as an array)
            target_strength = ts_length_regression(
                length["length"], length["TS_L_slope"], length["TS_L_intercept"]
            )
            # ---- Convert to `sigma_bs`
            sigma_bs_value = to_linear(target_strength)
            # ---- Weighted or arithmetic avveraging
            if weights is None:
                return sigma_bs_value.mean()
            elif weights not in length.columns:
                raise ValueError(
                    f"Defined `weights` column, {weights}, missing from dataframe input "
                    f"`length`."
                )
            else:
                return (sigma_bs_value * length[weights]).sum() / length[weights].sum()


# TODO: Documentation
# TODO: Refactor
def estimate_echometrics(acoustic_data_df: pd.DataFrame):

    # Create copy
    acoustic_df = acoustic_data_df.copy().reset_index(drop=True)

    # Compute ABC
    # ---- Convert NASC to ABC
    acoustic_df["ABC"] = acoustic_df["NASC"] / (4 * np.pi * 1852**2)

    # Pre-compute the change in depth
    acoustic_df["dz"] = acoustic_df["depth"].diff()
    # ---- Change first cell !
    acoustic_df.loc[0, "dz"] = acoustic_df.loc[1, "depth"] - acoustic_df.loc[0, "depth"]

    # Initialize echometrics dictionary
    echometrics = {}

    # Compute the metrics center-of-mass
    if acoustic_df["NASC"].sum() == 0.0:
        echometrics.update(
            {
                "n_layers": 0,
                "mean_Sv": -999,
                "max_Sv": -999,
                "nasc_db": np.nan,
                "center_of_mass": np.nan,
                "dispersion": np.nan,
                "evenness": np.nan,
                "aggregation_index": np.nan,
                "occupied_area": 0.0,
            }
        )
    else:

        # Create the `echometrics` dictionary
        echometrics.update(
            {
                # ---- Number of layers
                "n_layers": int(acoustic_df["depth"][acoustic_df["NASC"] > 0.0].size),
                # ---- Mean Sv (back-calculated)
                "mean_Sv": float(
                    10.0 * np.log10(acoustic_df["ABC"].sum() / acoustic_df["depth"].max())
                ),
                # ---- Max Sv (back-calculated)
                "max_Sv": float(
                    10
                    * np.log10(
                        acoustic_df["ABC"].max()
                        / acoustic_df.loc[np.argmax(acoustic_df["ABC"]), "dz"]
                    )
                ),
                # ---- (Logarithmic) acoustic abundance
                "nasc_db": float(10 * np.log10(acoustic_df["ABC"].sum())),
                # ---- Center-of-mass
                "center_of_mass": float(
                    (acoustic_df["depth"] * acoustic_df["NASC"]).sum() / (acoustic_df["NASC"]).sum()
                ),
                # ---- Evenness
                "evenness": float(
                    (acoustic_df["NASC"] ** 2).sum() / ((acoustic_df["NASC"]).sum()) ** 2
                ),
                # ---- Occupied area
                "occupied_area": float(
                    acoustic_df["dz"][acoustic_df["ABC"] > 0.0].sum() / acoustic_df["depth"].max()
                ),
            }
        )

        # Update variable-dependent metrics
        echometrics.update(
            {
                # ---- Dispersion
                "dispersion": float(
                    (
                        (acoustic_df["depth"] - echometrics["center_of_mass"]) ** 2
                        * acoustic_df["NASC"]
                    ).sum()
                    / (acoustic_df["NASC"]).sum()
                ),
                # ---- Index of aggregation
                "aggregation_index": float(1 / echometrics["evenness"]),
            }
        )

    # Return the dictionary
    return echometrics


def integrate_nasc(data_df: pd.DataFrame, echometrics: bool = True):

    # Vertically integrate PRC NASC
    nasc_dict = {"nasc": data_df["NASC"].sum()}

    # Horizontally concatenate `echometrics`, if `True`
    if echometrics:
        # ---- Compute values
        # NOTE: This uses NASC instead of linear `sv`
        echometrics_dict = estimate_echometrics(data_df)
        # ---- Merge
        nasc_dict.update(echometrics_dict)

    # Convert `nasc_dict` to a DataFrame and return the output
    # return pd.Series(nasc_dict)
    return pd.DataFrame(nasc_dict, index=[0])

    # return pd.DataFrame([nasc_dict])


def compute_nasc(
    acoustic_data_df: pd.DataFrame, file_configuration: dict, echometrics: bool = True
):

    # Get spatial definitions, if any
    # spatial_column = file_configuration["spatial_column"]

    # Get stratum column, if any
    gridding_column = file_configuration["gridding_column"]

    # Integrate NASC (and compute the echometrics, if necessary)
    # ---- Get number of unique sources
    # if len(np.unique(acoustic_data_df["ping_time"])) > 1:
    #     nasc_data_df = (
    #         acoustic_data_df
    #         .groupby(["longitude", "latitude", "ping_time", "source"] + spatial_column,
    #                  observed=False)
    #         .apply(integrate_nasc, echometrics, include_groups=False).unstack()
    #         .reset_index()
    #         .sort_values("ping_time")
    #     )
    # else:
    nasc_data_df = (
        acoustic_data_df.groupby(
            ["ship_id", "longitude", "latitude", "ping_time", "source"] + gridding_column,
            observed=False,
        )
        .apply(integrate_nasc, echometrics, include_groups=False)
        .droplevel(-1)
        .reset_index()
        .sort_values("ping_time")
    )
    # ---- Amend the dtypes if echometrics were computed
    if echometrics:
        # ---- Set dtypes
        nasc_data_df = nasc_data_df.astype(
            {
                "n_layers": int,
                "mean_Sv": float,
                "max_Sv": float,
                "nasc_db": float,
                "center_of_mass": float,
                "dispersion": float,
                "evenness": float,
                "aggregation_index": float,
                "occupied_area": float,
            }
        )
        # ---- Reorder columns
        nasc_data_df = nasc_data_df[
            gridding_column
            + [
                "ship_id",
                "longitude",
                "latitude",
                "ping_time",
                "source",
                "nasc",
                "n_layers",
                "nasc_db",
                "mean_Sv",
                "max_Sv",
                "aggregation_index",
                "center_of_mass",
                "dispersion",
                "evenness",
                "occupied_area",
            ]
        ]

    # Return the output
    return nasc_data_df


def format_acoustic_dataset(nasc_data_df: pd.DataFrame, file_configuration: dict, meta_dict: dict):

    # Get acoustic database filename
    acoustic_db = file_configuration["database"]["acoustics"]

    # Create a copy of the dataframe
    df = nasc_data_df.copy()

    # Add population-specific columns (specified in the file configuration)
    # TODO: Add to `yaml` file for configuration; hard-code for now
    add_columns = ["number_density", "biomass_density"]
    # ----
    df[add_columns] = 0.0
    # ---- Assign values for key values
    key_values = [
        f"{df.loc[index, 'ship_id']}-{str(index)}-{df.loc[index, 'source']}" for index in df.index
    ]
    # ---- Add an autoincrementing tag that will serve as a primary key and unique constraint
    df.loc[:, "id"] = key_values

    # Get root database directory
    root_database = file_configuration["database_directory"]

    # Update the successfully processed files
    query_processed_files(
        root_database,
        file_configuration["input_directories"]["acoustics"],
        meta_dict["provenance"]["acoustic_files_read"],
        processed=True,
    )

    # Insert the new data into the database & pull in the combined dataset
    # TODO: Replace with single-direction INSERT statement instead of INSERT/SELECT
    _ = sql_data_exchange(
        acoustic_db,
        dataframe=df,
        table_name="survey_data_df",
        id_columns=["id"],
        primary_keys=["id"],
        output_type=pd.DataFrame,
    )

    # Return the formatted dataframe
    return df
