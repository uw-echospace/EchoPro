from functools import reduce

import numpy as np
import pandas as pd

from ..utils.operations import group_interpolator_creator
from .live_acoustics import average_sigma_bs
from .live_spatial_methods import apply_spatial_definitions
from .sql_methods import (
    SQL,
    get_table_key_names,
    sql_data_exchange,
    sql_group_update,
    sql_update_strata_summary,
)


def biology_data_filter(biology_data: pd.DataFrame, filter_dict: dict):

    # Create dataframe copy
    data_copy = biology_data.copy()

    # Iterate through dictionary to apply filters (if present)
    for column, value in filter_dict.items():
        if column in data_copy.columns:
            data_copy = data_copy[data_copy[column] == value]

    # Return output
    return data_copy


def merge_trawl_info(biology_dict: dict):

    # Get the trawl information dictionary
    trawl_info_df = biology_dict["trawl_info_df"]

    # Update `catch_df`
    biology_dict["catch_df"] = biology_dict["catch_df"].merge(trawl_info_df)

    # Update `length_df`
    biology_dict["length_df"] = biology_dict["length_df"].merge(trawl_info_df)

    # Update `specimen_df`
    biology_dict["specimen_df"] = biology_dict["specimen_df"].merge(trawl_info_df)

    # Drop the trawl information
    del biology_dict["trawl_info_df"]


def prepare_length_distribution(file_configuration: dict):

    # Get the length distribution parameters
    distrib_params = file_configuration["biology"]["length_distribution"]["bins"]

    # Create histogram bins
    length_bins = np.linspace(
        **{key: value for key, value in zip(["start", "stop", "num"], distrib_params)}, dtype=float
    )

    # Get the binwidths
    binwidth = np.diff(length_bins / 2.0).mean()

    # Generate the equivalent interval boundaries for each bin
    intervals = np.concatenate([length_bins[:1] - binwidth, length_bins + binwidth])

    # Format as a DataFrame and return the output
    # ---- Add Categorical interval column
    length_bins_df = pd.DataFrame(
        {"length_bin": length_bins, "interval": pd.cut(length_bins, intervals)}
    )
    # ---- Add numeric lower boundary
    length_bins_df["lower"] = length_bins_df["interval"].apply(lambda x: x.left).astype(float)
    # ---- Add numeric upper boundary
    length_bins_df["upper"] = length_bins_df["interval"].apply(lambda x: x.right).astype(float)

    # Return the dataframe that will be incorporated into the biological data attribute
    return length_bins_df


def preprocess_biology_data(biology_output: dict, spatial_dict: dict, file_configuration: dict):

    # Get SQL database file
    biology_db = file_configuration["database"]["biology"]

    # Get contrasts used for filtering the dataset
    # ---- Species
    species_filter = file_configuration["species"]["number_code"]
    # ---- Trawl partition information
    trawl_filter = file_configuration["biology"]["catch"]["partition"]
    # ---- Create filter dictionary
    filter_dict = dict(species_id=species_filter, trawl_partition=trawl_filter)

    # Apply the filter
    filtered_biology_output = {
        key: biology_data_filter(df, filter_dict)
        for key, df in biology_output.items()
        if isinstance(df, pd.DataFrame) and not df.empty
    }
    # ---- Create new data flag
    file_configuration["length_distribution"] = prepare_length_distribution(file_configuration)
    # ---- Incorporate additional data, if new data are present
    if filtered_biology_output:
        # ---- Merge the trawl information and app
        merge_trawl_info(filtered_biology_output)
        # ---- Apply spatial definitions/stratification, if any
        apply_spatial_definitions(filtered_biology_output, spatial_dict)
    # ---- Swap this out if no new files are present
    if not filtered_biology_output:
        # ---- Get available tables
        table_list = list(set(SQL(biology_db, "map")) - set(["files_read"]))
        # ---- Plug into the dictionary
        filtered_biology_output.update({key: pd.DataFrame() for key in table_list})
    # ---- Initialize the results dictionary
    sql_results_dict = {key: pd.DataFrame() for key in filtered_biology_output.keys()}

    # Update the SQL database
    for table_name, df in filtered_biology_output.items():
        # ---- Get identifier columns
        key_columns = get_table_key_names(biology_db, filtered_biology_output, table_name)
        # ---- Create copy
        df = df.copy()
        # ---- Assign values for key values
        key_values = [
            str(index) + "-" + "-".join(df.loc[index, key_columns].values.astype(str))
            for index in df.index
        ]
        # ---- Add an autoincrementing tag that will serve as a primary key and unique constraint
        df.loc[:, "id"] = key_values
        # ---- Insert the new data into the database & pull in the combined dataset
        table_df = sql_data_exchange(
            biology_db,
            dataframe=df,
            table_name=table_name,
            id_columns=["id"],
            primary_keys=["id"],
            output_type=pd.DataFrame,
        )
        # ---- Drop SQL db identifier
        if "id" in table_df.columns:
            table_df.drop(columns="id", inplace=True)
        # ---- Add to the outgoing dictionary
        sql_results_dict.update({table_name: table_df})

    # Return the output
    return filtered_biology_output, sql_results_dict


def compute_sigma_bs(
    specimen_data: pd.DataFrame, length_data: pd.DataFrame, file_configuration: dict
):

    # Determine contrast columns
    # ----- Check for "stratum" column in spatial definitions configuration
    stratum_column = file_configuration["spatial_column"]
    # ---- Append to other defined keys
    contrast_columns = stratum_column + ["haul_num", "species_id", "length"]

    # Meld the biological datasets
    length_datasets = specimen_data.meld(length_data, contrasts=contrast_columns)

    # Get the TS-length model parameterization
    ts_length_parameters_spp = [
        spp
        for spp in file_configuration["acoustics"]["TS_length_regression_parameters"].values()
        if spp["number_code"] in np.unique(length_datasets.species_id).astype(int)
    ]

    # Extract the target species information
    target_species = pd.DataFrame.from_dict(ts_length_parameters_spp)
    # ---- Filter out non-target species
    length_datasets = length_datasets[
        length_datasets["species_id"].isin(target_species["number_code"])
    ]
    # ---- Merge with `length_datasets`
    ts_length_df = length_datasets.merge(
        target_species, left_on=["species_id"], right_on=["number_code"]
    )

    # Compute the mean sigma_bs for this particular haul
    # ---- Create primary key list
    key_list = list(set(contrast_columns) - set(["length"]))
    # ---- Compute haul-specific means
    sigma_bs_df = (
        ts_length_df.groupby(key_list, observed=False)[
            ["TS_L_slope", "TS_L_intercept", "length", "length_count"]
        ]
        .apply(lambda x: average_sigma_bs(x, weights="length_count"))
        .to_frame("sigma_bs")
    )

    # For SQL database storage purposes, the sum and count are stored instead
    # ---- Count sum
    sigma_bs_df["sigma_bs_count"] = (
        ts_length_df.reset_index().groupby(key_list, observed=False)["length_count"].sum()
    )
    # ---- Value sum
    sigma_bs_df["sigma_bs_sum"] = sigma_bs_df["sigma_bs"] * sigma_bs_df["sigma_bs_count"]
    # ---- Reset index
    sigma_bs_df = sigma_bs_df.reset_index()
    # ---- Create a tuple-key that can be used as an identifier
    sigma_bs_df.loc[:, "id"] = sigma_bs_df[key_list].apply(tuple, axis=1).astype(str)

    # Get the database file name
    biology_db = file_configuration["database"]["biology"]

    # Check for `sigma_bs_mean_df` in the database file
    # ---- Query database
    if not SQL(biology_db, "validate", table_name="sigma_bs_mean_df"):
        # ---- Create an insertion dataframe
        insertion_df = sigma_bs_df.copy()
        # ---- Create
        SQL(
            biology_db,
            "create",
            table_name="sigma_bs_mean_df",
            dataframe=insertion_df,
            primary_keys=key_list + ["id"],
        )
        # ---- Populate table
        SQL(
            biology_db,
            "insert",
            table_name="sigma_bs_mean_df",
            dataframe=insertion_df,
            id_columns=key_list + ["id"],
        )
    else:
        # ---- Get previous values in the table
        table_df = SQL(biology_db, "select", table_name="sigma_bs_mean_df")
        # ---- Check the table keys
        table_keys = np.unique(table_df["id"]).tolist()
        # ---- Get unique values
        current_keys = np.unique(sigma_bs_df["id"]).tolist()
        # ---- Get INSERTION keys
        insertion_keys = list(set(current_keys).difference(set(table_keys)))
        # ---- Get UPDATE keys
        update_keys = list(set(current_keys).intersection(set(table_keys)))
        # ---- INSERT values
        if insertion_keys:
            # ---- Create DataFrame
            insertion_df = sigma_bs_df[sigma_bs_df["id"].isin(insertion_keys)]
            # ---- INSERT
            SQL(biology_db, "insert", table_name="sigma_bs_mean_df", dataframe=insertion_df)
        # ---- UPDATE values
        if update_keys:
            update_df = sigma_bs_df[sigma_bs_df["id"].isin(update_keys)]
            # ---- Create a filter condition command
            sql_group_update(
                biology_db,
                dataframe=update_df,
                table_name="sigma_bs_mean_df",
                columns=["sigma_bs_count", "sigma_bs_sum"],
                operation="+",
                unique_columns=["id"],
                id_columns=["id"],
            )
            # condition_str = " & ".join([f"id = {id_value}" for id_value in update_keys])

        #     SQL(acoustic_db, "update", table_name="sigma_bs_mean_df", dataframe=update_df,
        #         operation="+", columns=["sigma_bs_count", "sigma_bs_sum"],
        #         condition=condition_str)
        #             # ---- Check the present keys
        # current_keys_dict = SQL(acoustic_db, "inspect", table_name="sigma_bs_mean_df",
        #                         columns=key_list)
        # # ---- Insert if missing
        # if not all([all(sigma_bs_df[key].isin(current_keys_dict[key])) for key in key_list]):
        #     SQL(acoustic_db, "insert", table_name="sigma_bs_mean_df", dataframe=sigma_bs_df)
        # # ---- Update if not missing
        # else:
        #     # ---- Create a filter condition command
        # condition_str = " & ".join([f"{key} in {np.unique(sigma_bs_df[key])}" for key inkey_list])
        #     # ---- Update the table key
        #    SQL(acoustic_db, "update", table_name="sigma_bs_mean_df", dataframe=sigma_bs_df,
        #       operation="+", columns=["sigma_bs_count", "sigma_bs_sum"], condition=condition_str)
        #     # ---- Update the actual `sigma_bs` value in the table
        #     SQL(acoustic_db, "update", table_name="sigma_bs_mean_df", columns=["sigma_bs"],
        #         operation="sigma_bs_sum / sigma_bs_count", condition=condition_str)


def length_weight_regression(
    specimen_data: pd.DataFrame, distribution_df: pd.DataFrame, file_configuration: dict
):

    # Get the spatial column name, if there is one
    spatial_column = file_configuration["spatial_column"].copy()
    # ---- Append additional columns that will be used
    contrast_columns = spatial_column + [
        "trawl_partition",
        "sex",
        "haul_num",
        "species_id",
        "length_bin",
    ]

    # Gather specimen measurements to represent 'all' fish
    specimen_data_all = specimen_data.assign(sex="all")

    # Combine sexed and 'all' specimens
    # ---- Vertical concatenation
    specimen_data_all = pd.concat(
        [specimen_data[specimen_data["sex"].isin(["male", "female"])], specimen_data_all],
        ignore_index=True,
    )
    # ---- Remove bad values
    specimen_data_all.dropna(subset=["length", "weight"], inplace=True)

    # Get SQL database file
    biology_db = file_configuration["database"]["biology"]

    # Check for `specimen_data_df` in the database file
    # ---- Query database
    # if not SQL(biology_db, "validate", table_name="specimen_data_df"):
    # ---- Assign values for key values
    key_values = [
        str(index)
        + "-"
        + "-".join(specimen_data_all.loc[index, contrast_columns].values.astype(str))
        for index in specimen_data_all.index
    ]
    # ---- Add an autoincrementing tag that will serve as a primary key and unique constraint
    specimen_data_all.loc[:, "id"] = key_values
    # ---- Insert the new data into the database & pull in the combined dataset
    specimen_data_sql = sql_data_exchange(
        biology_db,
        dataframe=specimen_data_all,
        table_name="specimen_data_df",
        id_columns=["id"],
        primary_keys=["id"],
        output_type=pd.DataFrame,
    )
    # ---- Drop SQL db identifier
    specimen_data_sql.drop(columns="id", inplace=True)

    # Fit length-weight linear regression by male, female, and all fish
    length_weight_regression_df = (
        specimen_data_sql.groupby(["species_id", "sex"])
        .apply(
            lambda df: pd.Series(
                np.polyfit(np.log10(df["length"]), np.log10(df["weight"]), 1),
                index=["rate", "initial"],
            ),
            # include_groups=False,
        )
        .reset_index()
    )

    # Predict weights for binned lengths
    # ---- Initialize dataframe
    weight_fitted_df = distribution_df.copy()
    # ---- Expand/merge with length-weight regression coefficients
    weight_fitted_df = weight_fitted_df.merge(length_weight_regression_df, how="cross")
    # ---- Predict weight per bin
    weight_fitted_df["weight_modeled"] = (
        10.0 ** weight_fitted_df["initial"]
        * weight_fitted_df["length_bin"] ** weight_fitted_df["rate"]
    )
    # ---- Drop unused columns
    weight_fitted_df = weight_fitted_df.filter(
        ["length_bin", "species_id", "sex", "weight_modeled"]
    )

    # Adjust for cases where there are too few (< 5) specimens within a given length bin
    # ---- Count number of specimens across length bins
    weight_fitted_distribution_df = specimen_data_all.count_variable(
        contrasts=["species_id", "sex", "length_bin"], variable="length", fun="size"
    ).set_index(["species_id", "sex", "length_bin"])
    # ---- Get mean weight per bin as well
    weight_fitted_distribution_df["weight_mean"] = (
        specimen_data_all.groupby(["species_id", "sex", "length_bin"], observed=False)["weight"]
        .mean()
        .fillna(0.0)
    )
    # ---- Merge with the fitted weights
    weight_fitted_distribution_df = weight_fitted_distribution_df.merge(
        weight_fitted_df, on=["species_id", "sex", "length_bin"], how="outer"
    )
    # ---- Fill missing counts
    weight_fitted_distribution_df["weight_mean"] = weight_fitted_distribution_df[
        "weight_mean"
    ].fillna(0.0)
    # ---- Fill missing weights
    weight_fitted_distribution_df["count"] = (
        weight_fitted_distribution_df["count"].fillna(0).astype(int)
    )
    # ---- Find fitted weights accounting for low sample sizes
    weight_fitted_distribution_df["weight_fitted"] = np.where(
        weight_fitted_distribution_df["count"] < 5,
        weight_fitted_distribution_df["weight_modeled"],
        weight_fitted_distribution_df["weight_mean"],
    )
    # ---- Pull out unused columns
    weight_fitted_distribution_df = weight_fitted_distribution_df.filter(
        ["species_id", "sex", "length_bin", "weight_fitted"]
    )

    # Check for `weight_fitted_df` in the database file
    # ---- Create id/primary key
    key_values = [
        "-".join(
            weight_fitted_distribution_df.loc[
                idx, ["species_id", "sex", "length_bin"]
            ].values.astype(str)
        )
        for idx in weight_fitted_distribution_df.index
    ]
    # ---- Add to the output
    output_df = weight_fitted_distribution_df.assign(id=key_values)
    # ---- Query database
    if not SQL(biology_db, "validate", table_name="weight_fitted_df"):
        # ---- Create
        SQL(
            biology_db,
            "create",
            table_name="weight_fitted_df",
            dataframe=output_df,
            primary_keys=["id"],
        )
        # ---- Populate table
        SQL(
            biology_db,
            "insert",
            table_name="weight_fitted_df",
            dataframe=output_df,
            id_columns=["id"],
        )
    else:
        # ---- Update the table
        sql_group_update(
            db_file=biology_db,
            dataframe=output_df,
            table_name="weight_fitted_df",
            columns=["weight_fitted"],
            unique_columns=["species_id", "sex", "length_bin"],
            id_columns=["id"],
        )

    # Return the dataframe
    return weight_fitted_distribution_df


def length_bin_weights(
    length_data: pd.DataFrame,
    specimen_data: pd.DataFrame,
    length_weight_df: pd.DataFrame,
    file_configuration: dict,
):

    # Get the spatial column name, if there is one
    contrast_columns = file_configuration["spatial_column"].copy()
    # ---- Get the spatial key
    # spatial_key = contrast_columns.copy()
    # ---- Append additional columns that will be used
    contrast_columns.extend(["sex", "species_id"])

    # Get database
    biology_db = file_configuration["database"]["biology"]

    # Pull the relevant data
    # SQL(biology_db, "select", table_name="length_df",
    #     columns=list(set(length_data.columns) - set(["length_bin"])))
    # list(set(length_data.columns) - set(["length_bin"]))
    # Get length distribution
    distribution_df = file_configuration["length_distribution"]

    # Generate sex-specific interpolators for fitted length-weight values for binned length counts
    # ---- Parse the male- and female-specific fitted weight values
    length_weight_sex = length_weight_df.copy()[length_weight_df["sex"].isin(["male", "female"])]
    # ---- Create interpolator functions
    interpolators = group_interpolator_creator(
        grouped_data=length_weight_sex,
        independent_var="length_bin",
        dependent_var="weight_fitted",
        contrast=["sex", "species_id"],
    )

    # ---- Create helper/lambda function
    def weight_interpolator(dataframe_row):
        sex = dataframe_row["sex"]
        species_id = dataframe_row["species_id"]
        length = dataframe_row["length"]
        if (sex, species_id) in interpolators:
            return interpolators[(sex, species_id)](length)
        else:
            return None

    # Extract only sexed fish from the unaged (station 1) length dataset
    length_data_sexed = length_data[length_data["sex"].isin(["male", "female"])].copy()
    # ---- Add interpolated weights to the general length dataset
    length_data_sexed.loc[:, "weight_interp"] = (
        length_data_sexed.apply(weight_interpolator, axis=1) * length_data_sexed["length_count"]
    )
    # ---- Convert interpolated weights (summed across length counts) into a table
    length_table_sexed = (
        length_data_sexed.groupby(list(set(contrast_columns).union(set(["length_bin"]))))[
            "weight_interp"
        ].sum()
    ).reset_index()

    # Remove specimen data with missing data required for this analysis
    # ---- Drop unsexed fish
    specimen_data_filtered = specimen_data[specimen_data["sex"].isin(["male", "female"])].copy()
    # ---- Remove NaN
    specimen_data_filtered = specimen_data_filtered.dropna(subset=["length", "weight"])
    # ---- Convert to a table
    specimen_table_sexed = (
        specimen_data_filtered.groupby(list(set(contrast_columns).union(set(["length_bin"]))))[
            "weight"
        ].sum()
    ).reset_index()

    # Check for `length_weight_df` in the database file
    # ---- Combine the datasets
    full_weight_distrib = pd.concat(
        [length_table_sexed.rename(columns={"weight_interp": "weight"}), specimen_table_sexed],
        ignore_index=True,
    )
    # ---- Sum by bin
    full_weight_distrib = (
        full_weight_distrib.groupby(contrast_columns + ["length_bin"])["weight"].sum().reset_index()
    )
    # ---- Create id/primary key
    full_weight_distrib.loc[:, "id"] = (
        full_weight_distrib[contrast_columns + ["length_bin"]]
        .apply(tuple, axis=1)
        .astype(str)
        .str.replace("'", "")
    )
    #
    key_values = [
        "-".join(
            length_table_sexed.reset_index()
            .loc[idx, ["species_id", "sex", "length_bin"]]
            .values.astype(str)
        )
        for idx in length_table_sexed.reset_index().index
    ]
    # ---- Add to the output
    length_table_sexed["id"] = key_values
    # ---- Query database
    if not SQL(biology_db, "validate", table_name="length_weight_df"):
        # ---- Create full table
        overall_weight_distrib = (
            pd.DataFrame(
                {
                    "stratum": file_configuration["geospatial"]["inpfc"]["stratum_names"]
                    + [len(file_configuration["geospatial"]["inpfc"]["stratum_names"]) + 1]
                }
            )
            .merge(pd.DataFrame({"sex": ["male", "female"]}), how="cross")
            .merge(
                pd.DataFrame(
                    {"species_id": np.unique(file_configuration["species"]["number_code"])}
                ),
                how="cross",
            )
            .merge(distribution_df.filter(["length_bin"]), how="cross")
        )
        # ---- Pre-allocate weight
        overall_weight_distrib.loc[:, "weight"] = 0.0
        # ---- Create id/primary key
        overall_weight_distrib.loc[:, "id"] = (
            overall_weight_distrib[contrast_columns + ["length_bin"]]
            .apply(tuple, axis=1)
            .astype(str)
            .str.replace("'", "")
        )
        # ---- Create
        SQL(
            biology_db,
            "create",
            table_name="length_weight_df",
            dataframe=overall_weight_distrib,
            primary_keys=["id"],
        )
        # ---- INSERT
        SQL(biology_db, "insert", table_name="length_weight_df", dataframe=overall_weight_distrib)
    # ---- UPDATE
    sql_group_update(
        biology_db,
        dataframe=full_weight_distrib,
        table_name="length_weight_df",
        columns=["weight"],
        unique_columns=["id"],
        id_columns=["id"],
    )
    # table_df = SQL(biology_db, "select", table_name="length_weight_df")
    # # ---- Check the table keys
    # table_keys = np.unique(table_df["id"]).tolist()
    # # ---- Get unique values
    # current_keys = np.unique(full_weight_distrib["id"]).tolist()
    # # ---- Get INSERTION keys
    # insertion_keys = list(set(current_keys).difference(set(table_keys)))
    # # ---- Get UPDATE keys
    # update_keys = list(set(current_keys).intersection(set(table_keys)))
    #     # ---- INSERT values
    #     if insertion_keys:
    #         # ---- Create DataFrame
    #         insertion_df = full_weight_distrib[full_weight_distrib["id"].isin(insertion_keys)]
    #         # ---- INSERT
    #         SQL(biology_db, "insert", table_name="length_weight_df",
    #             dataframe=insertion_df)
    #     # ---- UPDATE values
    #     if update_keys:
    #         update_df = full_weight_distrib[full_weight_distrib["id"].isin(update_keys)]
    #         # ---- Create a filter condition command
    #         sql_group_update(biology_db, dataframe=update_df, table_name="length_weight_df",
    #                          columns=["weight"],
    #                          unique_columns=["id"], id_columns=["id"])

    #     # ---- Update the table
    #     sql_group_update(db_file=biology_db,
    #                      dataframe=length_table_sexed,
    #                      table_name="length_weight_df",
    #                      columns=["weight_interp"],
    #                      unique_columns=contrast_columns,
    #                      id_columns=["id"])
    # length_sql_sexed

    # , specimen_sql_sexed

    # Return outputs
    return length_table_sexed, specimen_table_sexed


def number_proportions(
    specimen_binned: pd.DataFrame,
    specimen_binned_filtered: pd.DataFrame,
    length_binned: pd.DataFrame,
    file_configuration: dict,
):

    # Get the spatial column name, if there is one
    contrast_columns = file_configuration["spatial_column"].copy()
    # ---- Append additional columns that will be used
    contrast_columns.extend(["sex", "species_id"])

    # Get unique values of each contrast column across the biological datasets
    dfs = [
        pd.DataFrame({col: df[col].unique().tolist()})
        for col, df in zip(
            contrast_columns, [specimen_binned, specimen_binned_filtered, length_binned]
        )
    ]
    # ---- Reduce into a single DataFrame
    count_total = reduce(lambda left, right: pd.merge(left, right, how="cross"), dfs)
    # ---- Set the indices
    count_total.set_index(contrast_columns, inplace=True)
    # ---- Specimen count
    count_total["total_specimen"] = specimen_binned.groupby(contrast_columns)["count"].sum()
    # ---- Specimen filtered count
    count_total["total_specimen_filtered"] = specimen_binned_filtered.groupby(contrast_columns)[
        "count"
    ].sum()
    # ---- Length count
    count_total["total_length"] = length_binned.groupby(contrast_columns)["count"].sum()
    # ---- Fill NaN
    count_total.fillna(0, inplace=True)
    count_total = count_total.reset_index().set_index(
        list(set(contrast_columns) - set(["sex", "species_id"]))
    )
    # ---- Grand totals
    count_total["total_overall"] = (
        count_total.loc[count_total.sex == "all", "total_specimen_filtered"]
        + count_total.loc[count_total.sex == "all", "total_length"]
    )
    # ---- Reset index
    count_total = count_total.reset_index()

    # Compute the number proportions for the specimen data
    specimen_number_proportion = specimen_binned_filtered[
        specimen_binned_filtered["sex"].isin(["male", "female", "all"])
    ].merge(
        count_total[
            list(set(contrast_columns).union(set(["total_specimen_filtered", "total_overall"])))
        ],
        on=contrast_columns,
    )
    # ---- Within-dataset proportion
    specimen_number_proportion["proportion_number_specimen"] = (
        specimen_number_proportion["count"] / specimen_number_proportion["total_specimen_filtered"]
    )
    # ---- Overall survey proportion
    specimen_number_proportion["proportion_number_specimen_overall"] = (
        specimen_number_proportion["count"] / specimen_number_proportion["total_overall"]
    )
    # ---- Compute the sex proportions
    sex_number_proportions = (
        specimen_number_proportion.groupby(contrast_columns, observed=False)[
            "proportion_number_specimen_overall"
        ]
        .sum()
        .reset_index()
    )

    # Compute the number proportions for the length data
    length_number_proportion = length_binned[
        length_binned["sex"].isin(["male", "female", "all"])
    ].merge(
        count_total[list(set(contrast_columns).union(set(["total_length", "total_overall"])))],
        on=contrast_columns,
    )
    # ---- Within-dataset proportion
    length_number_proportion["proportion_number_length"] = (
        length_number_proportion["count"] / length_number_proportion["total_length"]
    )
    # ---- Overall survey proportion
    length_number_proportion["proportion_number_length_overall"] = (
        length_number_proportion["count"] / length_number_proportion["total_overall"]
    )

    # Gather unaged (sexed) number proportions
    # ---- Merge
    sex_number_proportions = sex_number_proportions.merge(
        length_number_proportion.groupby(contrast_columns)["proportion_number_length_overall"]
        .sum()
        .reset_index(),
        how="outer",
    ).fillna(0.0)
    # ---- Sum overall total across datasets
    sex_number_proportions["proportion_number_overall"] = (
        sex_number_proportions.proportion_number_specimen_overall
        + sex_number_proportions.proportion_number_length_overall
    )

    # Return the output
    return specimen_number_proportion, length_number_proportion, sex_number_proportions


def length_bin_counts(
    length_data: pd.DataFrame, specimen_data: pd.DataFrame, file_configuration: dict
):

    # Get the spatial column name, if there is one
    contrast_columns = file_configuration["spatial_column"].copy()
    # ---- Append additional columns that will be used
    contrast_columns.extend(["sex", "species_id", "length_bin"])

    # Bin counts by sex
    # ---- Specimen
    specimen_number_distribution = pd.concat(
        [specimen_data, specimen_data.assign(sex="all")]
    ).count_variable(
        contrasts=contrast_columns,
        variable="length",
        fun="size",
    )
    # ---- Filter out unsexed data for parallel number counts and drop any NA's
    specimen_number_distribution_filtered = (
        pd.concat(
            [
                specimen_data[specimen_data.sex != "unsexed"],
                specimen_data[specimen_data.sex != "unsexed"].assign(sex="all"),
            ]
        )
        .dropna(subset=["length", "weight"])
        .count_variable(
            contrasts=contrast_columns,
            variable="length",
            fun="size",
        )
    )

    # Repeat for the aggregated data
    # ---- Length
    length_number_distribution = pd.concat(
        [length_data, length_data.assign(sex="all")]
    ).count_variable(
        contrasts=contrast_columns,
        variable="length_count",
        fun="sum",
    )

    return (
        specimen_number_distribution,
        specimen_number_distribution_filtered,
        length_number_distribution,
    )


# def length_bin_counts(biology_dict: dict, file_configuration: dict):

#     # Get the spatial column name, if there is one
#     contrast_columns = file_configuration["spatial_column"].copy()
#     # ---- Append additional columns that will be used
#     contrast_columns.extend(["sex", "species_id", "length_bin"])

#     # Get database file
#     biology_db = file_configuration["database"]["biology"]

#     # Get distribution data
#     distribution_df = file_configuration["length_distribution"]

#     # Generate number counts for the length distribution
#     length_datasets = (
#         biology_dict["specimen_df"]
#         .meld(biology_dict["length_df"],
#               contrasts=list(set(contrast_columns).union(["length_bin"])))
#     )
#     # ---- Create 'all'
#     length_datasets_all = pd.concat([
#         length_datasets[length_datasets["sex"].isin(["male", "female"])],
#         length_datasets.assign(sex="all")
#     ])

#     # Collapse by each bin
#     grouped_length = (
#         length_datasets_all
#         .groupby(contrast_columns, observed=False)["length_count"].sum()
#     )

#     # Get distinct DataFrame columns
#     distinct_keys = (
#         grouped_length
#         .reset_index()
#         .loc[:, list(set(contrast_columns) - set(["length_bin"]))].drop_duplicates()
#     )

#     # Create complete DataFrame
#     complete_distrib_df = (
#         distribution_df.merge(distinct_keys, how="cross").set_index(contrast_columns)
#     )
#     # ---- Pre-allocate the "length_count" column
#     complete_distrib_df.loc[:, "count"] = 0
#     # ---- Add the computed counts
#     complete_distrib_df.loc[grouped_length.index, "count"] = grouped_length
#     # ---- Create output DataFrame
#     output_df = complete_distrib_df.filter(["count"]).reset_index()

#     # Check for `length_count_df` in the database file
#     # ---- Create id/primary key
#     key_values = ["-".join(output_df
#                            .loc[idx, ["species_id", "sex", "length_bin"]]
#                            .values.astype(str))
#                 for idx in output_df.index]
#     # ---- Add to the output
#     output_df["id"] = key_values
#     # ---- Query database
#     if not SQL(biology_db, "validate", table_name="length_count_df"):
#         # ---- Create
#         SQL(biology_db, "create", table_name="length_count_df",
#             dataframe=output_df, primary_keys=["id"])
#         # ---- Populate table
#         SQL(biology_db, "insert", table_name="length_count_df",
#             dataframe=output_df, id_columns=["id"])
#     else:
#         # ---- Update the table
#         sql_group_update(db_file=biology_db,
#                          dataframe=output_df,
#                          table_name="length_count_df",
#                          columns=["count"],
#                          unique_columns=contrast_columns,
#                          id_columns=["id"])

#     # Return output
#     return output_df


def bin_length_data(biology_dict: dict, distribution_df: pd.DataFrame):

    # Create Lambda help function
    def _quantize_lengths(dataset, distribution):
        # ---- Cut/merge the underlying histogram/discretized length bins
        if "length" in dataset.columns:
            # ---- Cut the intervals
            dataset["length_bin"] = pd.cut(
                dataset["length"],
                np.unique(np.hstack([distribution["lower"], distribution["upper"]])),
                labels=distribution["length_bin"],
            ).astype(float)
        # ---- Return the dataset
        return dataset

    # Update the data dictionary
    biology_dict.update({k: _quantize_lengths(d, distribution_df) for k, d in biology_dict.items()})


def compute_average_weights(
    specimen_number_proportion: pd.DataFrame,
    length_number_proportion: pd.DataFrame,
    sex_number_proportions: pd.DataFrame,
    length_weight_df: pd.DataFrame,
    distribution_df: pd.DataFrame,
    file_configuration: dict,
):

    # Get the spatial column name, if there is one
    contrast_columns = file_configuration["spatial_column"].copy()
    # ---- Append additional columns that will be used
    contrast_columns.extend(["sex", "species_id"])

    overall_proportions = sex_number_proportions[sex_number_proportions["sex"] == "all"]
    updated_proportions = sex_number_proportions.copy()

    updated_proportions["number_proportion_length_all"] = overall_proportions[
        "proportion_number_length_overall"
    ].values[0]
    updated_proportions["number_proportion_specimen_all"] = overall_proportions[
        "proportion_number_specimen_overall"
    ].values[0]

    # Calculate the mixed aged and unaged number proportions
    updated_proportions["proportion_length"] = updated_proportions[
        "number_proportion_length_all"
    ] / (
        updated_proportions["number_proportion_length_all"]
        + updated_proportions["proportion_number_specimen_overall"]
    )
    # ---- Calculate aged number proportions per sex per stratum
    updated_proportions["proportion_specimen"] = updated_proportions[
        "proportion_number_specimen_overall"
    ] / (
        updated_proportions["proportion_number_specimen_overall"]
        + updated_proportions["proportion_length"]
    )
    # ---- Reduce the columns
    proportion_df = updated_proportions.filter(
        contrast_columns + ["proportion_length", "proportion_specimen"]
    )

    # Combine the aged-unaged (or station-specific) proportions for calculations
    # ---- Wide-to-long DataFrame
    station_proportions = pd.wide_to_long(
        proportion_df,
        stubnames="proportion",
        i=contrast_columns,
        j="group",
        sep="_",
        suffix="\\w+",
    ).reset_index()
    # ---- Convert to Table (to replicate indexed matrix operations)
    station_proportions_table = station_proportions.pivot_table(
        index=["species_id", "group", "sex"],
        columns=file_configuration["spatial_column"].copy(),
        values="proportion",
    ).fillna(0.0)

    # Calculate the number length proportions that will later be converted into weight
    # ---- Specimen
    specimen_length_distribution = (
        specimen_number_proportion.groupby(contrast_columns + ["length_bin"], observed=False)[
            "proportion_number_specimen"
        ]
        .sum()
        .reset_index(name="number_proportion")
    )
    # ---- Length
    length_length_distribution = length_number_proportion[
        length_number_proportion.sex != "unsexed"
    ][contrast_columns + ["length_bin", "proportion_number_length"]].rename(
        columns={"proportion_number_length": "number_proportion"}
    )

    # Get unique values of each contrast column across the biological datasets
    dfs = [
        pd.DataFrame({col: df[col].unique().tolist()})
        for col, df in zip(
            contrast_columns,
            [specimen_number_proportion, length_number_proportion, sex_number_proportions],
        )
    ]
    # ---- Reduce into a single DataFrame
    full_contrast_keys = reduce(lambda left, right: pd.merge(left, right, how="cross"), dfs)

    #
    length_distribution_df = distribution_df.copy()
    complete_distrib_df = (
        length_distribution_df.merge(full_contrast_keys, how="cross")
        .drop(columns=["interval", "lower", "upper"])
        .set_index(contrast_columns + ["length_bin"])
    )

    specimen_length_complete = complete_distrib_df.copy()
    specimen_length_complete["number_proportion"] = specimen_length_distribution.set_index(
        contrast_columns + ["length_bin"]
    ).sort_index()
    specimen_length_complete.loc[:, "number_proportion"] = specimen_length_complete[
        "number_proportion"
    ].fillna(0.0)

    length_length_complete = complete_distrib_df.copy()
    length_length_complete["number_proportion"] = length_length_distribution.set_index(
        contrast_columns + ["length_bin"]
    ).sort_index()
    length_length_complete.loc[:, "number_proportion"] = length_length_complete[
        "number_proportion"
    ].fillna(0.0)

    # ---- Concatenate the two datasets
    combined_number_proportions = (
        pd.concat(
            [
                specimen_length_complete.assign(group="specimen"),
                length_length_complete.assign(group="length"),
            ]
        )
    ).reset_index()
    # ---- Convert to Table (to replicate indexed matrix operations)
    length_proportions_table = combined_number_proportions.pivot_table(
        index=["species_id", "group", "sex", "length_bin"],
        columns=file_configuration["spatial_column"].copy(),
        values="number_proportion",
        observed=False,
    ).fillna(0.0)

    # Convert the fitteed weights into a Table (to replicate index matrix operations)
    fitted_weight_table = length_weight_df.pivot_table(
        index=["species_id", "sex", "length_bin"], values="weight_fitted", observed=False
    )

    # Calculate the average weights for male, female, and all fish within each stratum
    # ---- All
    fitted_weight_table.loc[:, "all", :]
    weight_all = fitted_weight_table.loc[:, "all", :]["weight_fitted"].values.dot(
        length_proportions_table.loc[:, "specimen", "all"]
        * station_proportions_table.loc[:, "specimen", "all"]
        + length_proportions_table.loc[:, "length", "all"]
        * station_proportions_table.loc[:, "length", "all"]
    )
    weight_male = fitted_weight_table.loc[:, "male", :]["weight_fitted"].values.dot(
        length_proportions_table.loc[:, "specimen", "male"]
        * station_proportions_table.loc[:, "specimen", "male"]
        + length_proportions_table.loc[:, "length", "male"]
        * station_proportions_table.loc[:, "length", "male"]
    )
    weight_female = fitted_weight_table.loc[:, "female", :]["weight_fitted"].values.dot(
        length_proportions_table.loc[:, "specimen", "female"]
        * station_proportions_table.loc[:, "specimen", "female"]
        + length_proportions_table.loc[:, "length", "female"]
        * station_proportions_table.loc[:, "length", "female"]
    )
    # ---- Combine the averaged weights for each sex and all fish
    fitted_weight_df = full_contrast_keys.copy()
    fitted_weight_df["average_weight"] = np.concatenate([weight_all, weight_male, weight_female])

    # Get database file
    biology_db = file_configuration["database"]["biology"]

    # Insert/update the table
    # ---- Create id/primary key
    key_values = [
        "-".join(fitted_weight_df.reset_index().loc[idx, contrast_columns].values.astype(str))
        for idx in fitted_weight_df.reset_index().index
    ]
    # ---- Add to the output
    fitted_weight_df["id"] = key_values
    if not SQL(biology_db, "validate", table_name="weight_stratum_df"):
        # ---- Create
        SQL(
            biology_db,
            "create",
            table_name="weight_stratum_df",
            dataframe=fitted_weight_df,
            primary_keys=["id"],
        )
        # ---- Populate table
        SQL(
            biology_db,
            "insert",
            table_name="weight_stratum_df",
            dataframe=fitted_weight_df,
            id_columns=["id"],
        )
    else:
        # ---- Get previous values in the table
        table_df = SQL(biology_db, "select", table_name="weight_stratum_df")
        # ---- Check the table keys
        table_keys = np.unique(table_df[contrast_columns].apply(tuple, axis=1)).tolist()
        # ---- Check the current keys
        fitted_weight_df["current_keys"] = fitted_weight_df[contrast_columns].apply(tuple, axis=1)
        # ---- Get unique values
        current_keys = np.unique(fitted_weight_df["current_keys"]).tolist()
        # ---- Get INSERTION keys
        insertion_keys = list(set(current_keys).difference(set(table_keys)))
        # ---- Get UPDATE keys
        update_keys = list(set(current_keys).intersection(set(table_keys)))
        # ---- INSERT values
        if insertion_keys:
            # ---- Create DataFrame
            insertion_df = fitted_weight_df[fitted_weight_df["current_keys"].isin(insertion_keys)]
            # ---- INSERT
            SQL(
                biology_db,
                "insert",
                table_name="weight_stratum_df",
                dataframe=insertion_df.drop(columns="current_keys"),
            )
        # ---- UPDATE values
        if update_keys:
            # ---- Create DataFrame
            update_df = fitted_weight_df[fitted_weight_df["current_keys"].isin(update_keys)]
            # ---- UPDATE
            sql_group_update(
                biology_db,
                dataframe=update_df,
                table_name="weight_stratum_df",
                columns=["average_weight"],
                unique_columns=contrast_columns,
                id_columns=["id"],
            )
    # Return output
    return fitted_weight_df


def weight_proportions(
    catch_data: pd.DataFrame,
    specimen_weight_binned: pd.DataFrame,
    length_weight_binned: pd.DataFrame,
    length_number_proportion: pd.DataFrame,
    length_weight_df: pd.DataFrame,
    file_configuration: dict,
):

    # Get the spatial column name, if there is one
    spatial_column = file_configuration["spatial_column"]
    # ---- Append additional columns that will be used
    contrast_columns = spatial_column + ["sex", "species_id"]

    # Calculate grouped totals
    # ---- Sum the net haul weights from station 1/unaged fish
    catch_weights = catch_data.count_variable(
        contrasts=["species_id"] + spatial_column, variable="haul_weight", fun="sum"
    )
    # ---- Rename resulting columns for both
    catch_weights.rename(columns={"count": "total_weight"}, inplace=True)

    # For the specimen data
    # ---- Sum the net haul weights from station 1/unaged fish
    specimen_weights_sex = specimen_weight_binned.groupby(contrast_columns)["weight"].sum()
    # ---- Total (per stratum, if it exists)
    specimen_weight_total = specimen_weights_sex.transpose().unstack(1).sum(axis=1)

    # For the length (unaged) dataset
    length_weights_sex = length_weight_binned.groupby(contrast_columns)["weight_interp"].sum()
    # ---- Further reduce to the grand total (per stratum, if it exists)
    length_weight_total = length_weights_sex.transpose().unstack(1).sum(axis=1)

    # ---- Standardize the unaged sexed weights
    length_weight_standardized = (length_weights_sex / length_weight_total).unstack(
        0
    ) * catch_weights["total_weight"].to_numpy()

    # Calculate the specimen weight proportions
    # ---- Pivot weight bins
    specimen_weight_binned_pvt = specimen_weight_binned.pivot_table(
        columns=spatial_column,
        index=["length_bin", "species_id", "sex"],
        values="weight",
        observed=False,
    )
    # ---- Divide by the aged stratum weights (relative to only aged fish)
    specimen_weight_proportions_pvt = specimen_weight_binned_pvt / specimen_weight_total.to_numpy()
    # ---- Pivot back to the desired format
    specimen_weight_proportion = (
        specimen_weight_proportions_pvt.stack()
        .reset_index(name="weight_proportion")
        .pivot_table(
            columns=spatial_column + ["species_id", "sex"],
            index="length_bin",
            values="weight_proportion",
        )
    )
    # ---- Calculate the internal (i.e. only aged fish) for each sex
    within_specimen_sex_proportions = specimen_weight_proportion.sum()

    # Calculate the total strata weights
    # ---- Index `catch_weights`
    catch_weights_idx = catch_weights.set_index(spatial_column + ["species_id"])
    # ---- Compute the spatially-stratified/grouped weights
    spatial_weights = pd.concat(
        [specimen_weight_total.to_frame("total_weight"), catch_weights_idx]
    ).pivot_table(columns=spatial_column, aggfunc="sum", values="total_weight", observed=False)

    # Calculate the weight proportions relative to the overall stratum weights
    # ---- Aged
    # -------- Reformat into dataframe and merge with total stratum weights
    specimen_weights_binned_df = (
        specimen_weight_binned_pvt.stack()
        .to_frame("specimen_weight")
        .reset_index()
        .merge(spatial_weights.T.reset_index(), on=spatial_column)
    )
    # -------- Calculate proportions
    specimen_weights_binned_df["weight_proportion_overall"] = (
        specimen_weights_binned_df["specimen_weight"] / specimen_weights_binned_df["total_weight"]
    )
    # -------- Consolidate to calculate the sexed proportions per stratum
    specimen_weight_sex_proportions = specimen_weights_binned_df.groupby(
        spatial_column + ["species_id", "sex"]
    )["weight_proportion_overall"].sum()
    # ---- Unaged
    # -------- Reformat into dataframe and merge with total stratum weights
    length_weights_sex_standardized_df = (
        length_weight_standardized.stack()
        .to_frame("catch_weight")
        .reset_index()
        .merge(spatial_weights.T.reset_index(), on=spatial_column)
    )
    # -------- Calculate proportions
    length_weights_sex_standardized_df["weight_proportion_overall"] = (
        length_weights_sex_standardized_df["catch_weight"]
        / length_weights_sex_standardized_df["total_weight"]
    )
    # -------- Back-calculate the sexed weight proportions relative to just unaged fish
    # ------------ Aggregate proportions
    length_total_sex_proportions = (
        length_weights_sex_standardized_df.pivot_table(
            columns=["species_id", "sex"], index=spatial_column, values="weight_proportion_overall"
        )
        .transpose()
        .unstack(["species_id"])
        .sum(axis=0)
    )
    # ------------ Re-compute the proportions
    length_weight_sex_proportions = (
        length_weights_sex_standardized_df.pivot_table(
            index=["species_id", "sex"], columns=spatial_column, values="weight_proportion_overall"
        )
        / length_total_sex_proportions.to_numpy()
    )

    # Compute the overall length-binned weight distributions among unaged fish
    # ---- Extract the number proportions computed for unaged fish
    length_number_proportions = length_number_proportion.copy()
    # ---- Filter out values besides those computed for 'all' fish
    length_number_proportions = length_number_proportions[length_number_proportions["sex"] == "all"]
    # ---- Convert to a table
    length_number_proportions_tbl = length_number_proportions.pivot_table(
        columns=spatial_column + ["species_id"],
        index=["length_bin"],
        values="proportion_number_length",
        aggfunc="sum",
        observed=False,
    )
    # ---- Extract the fitted weight values calculated for all fish
    length_weight_all = length_weight_df[length_weight_df["sex"] == "all"]
    # ---- Generate the fitted weight array
    fitted_weights = length_weight_all.copy()
    # ---- Get actual length bins in dataset
    fitted_weights = fitted_weights[
        fitted_weights["length_bin"].isin(length_number_proportions["length_bin"])
    ]
    # ---- Apportion the averaged weights
    length_apportioned_weights = (
        length_number_proportions_tbl.T * fitted_weights["weight_fitted"].to_numpy()
    )
    # ---- Compute the average weight proportions per length bin per stratum
    average_length_bin_weights = length_apportioned_weights.T / length_apportioned_weights.sum(
        axis=1
    )
    # ---- Convert back to a DataFrame
    average_length_bin_weights_df = average_length_bin_weights.unstack().reset_index(
        name="weight_proportion"
    )

    # Calculate the aged and unaged weight proportions
    # ---- Aged
    aged_proportions = specimen_weight_sex_proportions.unstack("sex").sum(axis=1)
    # ---- Unaged
    unaged_proportions = 1 - aged_proportions
    # -------- Re-weight the unaged sexed proportions
    unaged_weight_sex_proportions_overall = (
        (length_weight_sex_proportions * unaged_proportions.unstack().transpose())
        .astype(float)
        .fillna(0.0)
    )

    unaged_proportions.unstack().transpose()
    # Format the outputs
    # ---- Aged: stratum-sex-age-length relative to aged and total weights
    aged_overall_df = (
        specimen_weight_proportion.unstack()
        .reset_index(name="weight_proportions")
        .merge(
            specimen_weights_binned_df[
                spatial_column + ["length_bin", "sex", "species_id", "weight_proportion_overall"]
            ]
        )
    )
    # ---- Aged: stratum-sex relative to total weights
    aged_sex_df = within_specimen_sex_proportions.reset_index(
        name="weight_proportion_aged"
    ).set_index(spatial_column + ["species_id", "sex"])
    # ---- Add the aged sex proportiosn relative to the overall survey
    aged_sex_df["weight_proportion_overall_aged"] = specimen_weight_sex_proportions
    # ---- Consolidate the aged and unaged sexed dataframes
    # -------- Initialize the dataframe
    aged_unaged_sex_proportions = aged_sex_df.reset_index().set_index(
        ["species_id", "sex"] + spatial_column
    )
    # --------- Add the within-unaged weight proportions
    aged_unaged_sex_proportions["weight_proportion_unaged"] = length_weight_sex_proportions.stack()
    # --------- Add the overall-unaged weight proportions
    aged_unaged_sex_proportions["weight_proportion_overall_unaged"] = (
        unaged_weight_sex_proportions_overall.stack()
    )
    # ---- Overall aged and unaged proportions
    aged_unaged_proportions = aged_proportions.reset_index(name="aged_proportions")
    # ---- Set index
    aged_unaged_proportions.set_index(spatial_column + ["species_id"], inplace=True)
    # -------- Add unaged proportions
    aged_unaged_proportions["unaged_proportions"] = unaged_proportions  # .reset_index()
    # ---- Reset the index
    aged_unaged_proportions = aged_unaged_proportions.reset_index()

    # Return output
    return {
        "aged_weight_proportions_df": aged_overall_df,
        "unaged_weight_proportions_df": average_length_bin_weights_df,
        "aged_unaged_sex_weight_proportions_df": (
            aged_unaged_sex_proportions.astype(float).reset_index().fillna(0.0)
        ),
        "aged_unaged_weight_proportions_df": aged_unaged_proportions,
    }


# TODO: NEED TO UPDATE TO EITHER INSERT IF NOT PRESENT OR UPDATE OTHERWISE ! ! !
# ! SEE ABOVE
def summarize_strata(
    nasc_biology_data: pd.DataFrame, spatial_data: pd.DataFrame, file_configuration: dict
):

    # Get biology database
    acoustic_db = file_configuration["database"]["acoustics"]

    # Get biology database
    biology_db = file_configuration["database"]["biology"]

    # Validate table
    if not SQL(biology_db, "validate", table_name="strata_summary_df"):

        # Create copy
        strata_df = spatial_data.copy()

        # Define new columns
        strata_df[
            [
                "length_mean",
                "weight_mean",
                "TS_mean",
                "number_density_mean",
                "biomass_density_mean",
                "abundance_sum",
                "biomass_sum",
            ]
        ] = np.nan
        # ---- Drop 'latitude_interval'
        strata_df.drop(columns=["latitude_interval"], inplace=True)

        # ---- Create
        SQL(
            biology_db,
            "create",
            table_name="strata_summary_df",
            dataframe=strata_df,
            primary_keys=["stratum"],
        )
        # ---- Populate table
        SQL(
            biology_db,
            "insert",
            table_name="strata_summary_df",
            dataframe=strata_df,
            id_columns=["stratum"],
        )

    # Get unique strata values
    strata_values = np.unique(nasc_biology_data["stratum"]).tolist()

    # Update the table
    sql_update_strata_summary(
        source_db=acoustic_db,
        target_db=biology_db,
        source_table="survey_data_df",
        target_table="strata_summary_df",
        data_columns=[("number_density", "mean"), ("biomass_density", "mean")],
        strata=strata_values,
    )
