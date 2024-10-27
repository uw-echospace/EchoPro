from typing import List

import numpy as np
import pandas as pd

from .live_biology import summarize_strata
from .live_spatial_methods import update_population_grid
from .sql_methods import query_dataset, sql_group_update


def get_average_strata_weights(db_file: str, data_dict: dict, unique_columns: list):

    # Get corresponding `weight_fitted_df` from the database
    weight_fitted_sql_df = query_dataset(
        db_file,
        data_dict,
        table_name="weight_stratum_df",
        data_columns=unique_columns + ["average_weight"],
        unique_columns=unique_columns,
        constraint="sex == 'all'",
    )
    # ---- Use SQL table data if present
    if weight_fitted_sql_df is not None and not weight_fitted_sql_df.empty:
        # ---- Return output
        return weight_fitted_sql_df
    else:
        return None


def configure_database_paths(file_configuration: dict):

    # Extract input directory settings
    file_settings = file_configuration["input_directories"]

    # Get database directory
    database_dir = file_configuration["database_directory"]

    # Update configuration
    file_configuration["database"].update(
        {
            dataset: "/".join([database_dir, file_settings[dataset]["database_name"]])
            for dataset in file_settings.keys()
            if "database_name" in file_settings[dataset]
        }
    )


def acoustic_pipeline(
    acoustic_dict: dict,
    strata_df: pd.DataFrame,
    file_configuration: dict,
    verbose: bool,
    contrast_columns: List[str] = [],
):

    # Get spatial column
    spatial_column = file_configuration["spatial_column"]
    gridding_column = file_configuration["gridding_column"]
    unique_columns = gridding_column + contrast_columns

    # Get database file
    acoustic_db = file_configuration["database"]["acoustics"]

    # Get biology database file
    biology_db = file_configuration["database"]["biology"]

    # Check whether data dictionary is empty
    if acoustic_dict["nasc_df"] is None or acoustic_dict["nasc_df"].empty:
        # ---- Print, if verbose
        if verbose:
            print("No new processed acoustic data available for processing.")
    else:
        # Get related acoustic data
        acoustic_df = get_nasc_sql_data(acoustic_db, acoustic_dict, unique_columns=unique_columns)

        # Get the corresopding `sigma_bs` data (and also compute the sample-number weighted average)
        sigma_bs_df = get_sigma_bs_sql_data(biology_db, acoustic_dict, unique_columns=["stratum"])

        # Calculate population estimates if valid data are available
        if all([True if df is not None else False for df in [acoustic_df, sigma_bs_df]]):

            # ---- Merge the NASC and sigma_bs datasets
            nasc_biology = acoustic_df.merge(sigma_bs_df, on=spatial_column)
            # ---- Compute the number densities (animals nmi^-2)
            nasc_biology["number_density"] = nasc_biology["nasc"] / (
                4.0 * np.pi * nasc_biology["sigma_bs_mean"]
            )

            # Get the corresponding average strata weights (computed for all fish)
            weight_spatial_averages = get_average_strata_weights(
                biology_db, acoustic_dict, unique_columns=spatial_column + contrast_columns
            )

            if weight_spatial_averages is not None:
                # Merge average weights with number density estimates
                nasc_biology = nasc_biology.merge(weight_spatial_averages, on=spatial_column)

                # Compute biomass densities
                nasc_biology["biomass_density"] = (
                    nasc_biology["number_density"] * nasc_biology["average_weight"]
                )

            # Update the survey population estimate DataFrame with the newly computed densities
            if (
                all([True if df is not None else False for df in [acoustic_df, sigma_bs_df]])
                and not nasc_biology.empty
            ):
                sql_group_update(
                    acoustic_db,
                    dataframe=nasc_biology,
                    table_name="survey_data_df",
                    columns=["number_density", "biomass_density"],
                    unique_columns=["id"],
                )

                # Summarize strata
                summarize_strata(nasc_biology, strata_df, file_configuration)

                # Update grid
                update_population_grid(
                    file_configuration, coordinates=["x", "y"], dataset=nasc_biology
                )


def get_nasc_sql_data(db_file: str, data_dict: dict, unique_columns: List[str]):

    # Add SELECTION columns
    data_columns = unique_columns + [
        "longitude",
        "latitude",
        "ping_time",
        "nasc",
        "number_density",
        "biomass_density",
        "id",
    ]
    # ----- Get the SQL dataset
    nasc_sql_data = query_dataset(
        db_file,
        data_dict,
        table_name="survey_data_df",
        data_columns=data_columns,
        unique_columns=unique_columns,
        constraint="nasc > 0.0",
    )
    # ---- Use SQL table data if present
    if nasc_sql_data is not None and not nasc_sql_data.empty:
        return nasc_sql_data
    elif "nasc_df" in data_dict.keys():
        return data_dict["nasc_df"]


def get_sigma_bs_sql_data(db_file: str, data_dict: dict, unique_columns: list):

    # Get corresponding `sigma_bs` DataFrame
    sigma_bs_sql_df = query_dataset(
        db_file,
        data_dict,
        table_name="sigma_bs_mean_df",
        data_columns=unique_columns + ["sigma_bs", "sigma_bs_count"],
        unique_columns=unique_columns,
    )
    # ---- Use SQL table data if present
    if sigma_bs_sql_df is not None and not sigma_bs_sql_df.empty:
        # ---- Compute the weighted average
        sigma_bs_mean_sql_df = (
            sigma_bs_sql_df.groupby(unique_columns)[["sigma_bs", "sigma_bs_count"]]
            .apply(lambda df: np.average(df.sigma_bs, weights=df.sigma_bs_count))
            .to_frame("sigma_bs_mean")
            .reset_index()
        )
        # ---- Return output
        return sigma_bs_mean_sql_df
    else:
        return None


def biology_pipeline(
    biology_dict: dict,
    strata_df: pd.DataFrame,
    file_configuration: dict,
    verbose: bool,
    contrast_columns: List[str] = [],
):

    # Get spatial column
    spatial_column = file_configuration["spatial_column"]
    unique_columns = spatial_column + contrast_columns

    # Get database file
    acoustic_db = file_configuration["database"]["acoustics"]

    # Get biology database file
    biology_db = file_configuration["database"]["biology"]

    # Check for data completion
    # ---- List of boolean values
    full_biology_data = [
        True if (isinstance(df, pd.DataFrame) and not df.empty) or (isinstance(df, dict)) else False
        for _, df in biology_dict.items()
    ]
    # ---- Validation
    if not all(full_biology_data):
        # ---- Print, if verbose
        if verbose:
            print("No new processed biology data available for processing.")
    else:
        # Get related biology data
        acoustic_df = get_nasc_sql_data(acoustic_db, biology_dict, unique_columns=unique_columns)

        # Get the corresopding `sigma_bs` data (and also compute the sample-number weighted average)
        sigma_bs_df = get_sigma_bs_sql_data(biology_db, biology_dict, unique_columns=unique_columns)

        # Calculate population estimates if valid data are available
        if all([True if df is not None else False for df in [acoustic_df, sigma_bs_df]]):
            # ---- Merge the NASC and sigma_bs datasets
            nasc_biology = acoustic_df.merge(sigma_bs_df, on=unique_columns)
            # ---- Compute the number densities (animals nmi^-2)
            nasc_biology["number_density"] = nasc_biology["nasc"] / (
                4.0 * np.pi * nasc_biology["sigma_bs_mean"]
            )

            # Get the corresponding average strata weights (computed for all fish)
            weight_spatial_averages = get_average_strata_weights(
                biology_db, biology_dict, unique_columns=unique_columns
            )

            if weight_spatial_averages is not None:
                # Merge average weights with number density estimates
                nasc_biology = nasc_biology.merge(weight_spatial_averages, on=unique_columns)

                # Compute biomass densities
                nasc_biology["biomass_density"] = (
                    nasc_biology["number_density"] * nasc_biology["average_weight"]
                )

            # Update the survey population estimate DataFrame with the newly computed densities
            if not nasc_biology.empty:
                sql_group_update(
                    acoustic_db,
                    dataframe=nasc_biology,
                    table_name="survey_data_df",
                    columns=["number_density", "biomass_density"],
                    unique_columns=["stratum", "longitude", "latitude", "ping_time"],
                )

                # Summarize strata
                summarize_strata(nasc_biology, strata_df, file_configuration)

                # Update population grid
                update_population_grid(
                    file_configuration, coordinates=["stratum"], dataset=nasc_biology
                )
