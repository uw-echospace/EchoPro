from typing import List, Tuple, Union

import numpy as np
import pandas as pd

from .utils.operations import group_interpolator_creator


def filter_species(
    dataframe_list: Union[List[pd.DataFrame], pd.DataFrame], species_id: Union[int, List[int]]
) -> Tuple[pd.DataFrame]:
    """
    Filter species in one or multiple biological datasets

    Parameters
    ----------
    dataframe_list: Union[List[pd.DataFrame], pd.DataFrame]
        A list of dataframes or a single dataframe containing biological data/measurements
    species_id: Union[float, List[float]]
        A scalar or list of numeric codes representing particular species of interest
    """

    # If a single dataframe, convert to a list
    if isinstance(dataframe_list, pd.DataFrame):
        dataframe_list = [dataframe_list]

    # Change `species_id` to a list, if necessary
    if not isinstance(species_id, list):
        species_id = [species_id]

    # Filter out the species-of-interest
    filtered_dataframes = tuple(df[df["species_id"].isin(species_id)] for df in dataframe_list)

    # Return output
    return filtered_dataframes


def fit_length_weight_relationship(
    specimen_data: pd.DataFrame, length_distribution: pd.DataFrame
) -> dict:
    """
    Fit a length-weight relationship across discrete bins

    Parameters
    ----------
    specimen_data : pd.DataFrame
        Dataframe containing aged length and weight data.
    length_distribution: pd.DataFrame
        Dataframe containing the overall quantized length bins and intervals.

    Notes
    -----
    This function first fits a length-weight regression based on measured
    values and then produces an array of fitted weight values based on
    binned length values. The length-weight relationship produced here are used for later
    biomass calculations and apportionment.
    """

    # Gather specimen measurements to represent 'all' fish
    specimen_data_all = specimen_data.assign(sex="all")

    # Combine sexed and 'all' specimens
    # ---- Vertical concatenation
    specimen_data_all = pd.concat(
        [specimen_data[specimen_data.group_sex == "sexed"], specimen_data_all]
    )
    # ---- Remove bad values
    specimen_data_all.dropna(subset=["length", "weight"], inplace=True)

    # Fit length-weight linear regression by male, female, and all fish
    length_weight_regression_df = (
        specimen_data_all.groupby(["species_id", "sex"])
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
    weight_fitted_df = length_distribution.copy()
    # ---- Expand/merge with length-weight regression coefficients
    weight_fitted_df = weight_fitted_df.merge(length_weight_regression_df, how="cross")
    # ---- Predict weight per bin
    weight_fitted_df["weight_modeled"] = (
        10.0 ** weight_fitted_df["initial"]
        * weight_fitted_df["length_bins"] ** weight_fitted_df["rate"]
    )
    # ---- Drop unused columns
    weight_fitted_df = weight_fitted_df.filter(
        ["length_intervals", "species_id", "sex", "weight_modeled"]
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
        weight_fitted_df,
        left_on=["species_id", "sex", "length_bin"],
        right_on=["species_id", "sex", "length_intervals"],
    )
    # ---- Find fitted weights accounting for low sample sizes
    weight_fitted_distribution_df["weight_fitted"] = np.where(
        weight_fitted_distribution_df["count"] < 5,
        weight_fitted_distribution_df["weight_modeled"],
        weight_fitted_distribution_df["weight_mean"],
    )
    # ---- Pull out unused columns
    weight_fitted_distribution_df = weight_fitted_distribution_df.filter(
        ["species_id", "sex", "length_intervals", "weight_fitted"]
    )
    # Return output
    return {
        "length_weight_regression": {
            "parameters_df": length_weight_regression_df,
            "weight_fitted_df": weight_fitted_distribution_df,
        }
    }


def quantize_number_counts(
    specimen_data: pd.DataFrame, length_data: pd.DataFrame, stratum_column: str
) -> dict:
    """
    Quantize the number of animals belonging to each binned length and age

    Parameters
    ----------
    specimen_data : pd.DataFrame
        Dataframe containing aged length and weight data.
    length_data: pd.DataFrame
        Dataframe containing the overall quantized length bins and intervals.
    stratum_column: str
        Stratum column name.
    """

    # Bin counts by sex
    # ---- Aged
    aged_number_distribution = pd.concat(
        [specimen_data, specimen_data.assign(sex="all")]
    ).count_variable(
        contrasts=[stratum_column, "species_id", "sex", "length_bin", "age_bin"],
        variable="length",
        fun="size",
    )
    # ---- Filter out unsexed data for parallel number counts and drop any NA's
    aged_number_distribution_filtered = (
        pd.concat(
            [
                specimen_data[specimen_data.sex != "unsexed"],
                specimen_data[specimen_data.sex != "unsexed"].assign(sex="all"),
            ]
        )
        .dropna(subset=["length", "age", "weight"])
        .count_variable(
            contrasts=[stratum_column, "species_id", "sex", "length_bin", "age_bin"],
            variable="length",
            fun="size",
        )
    )
    # ---- Unaged
    unaged_number_distribution = pd.concat(
        [length_data, length_data.assign(sex="all")]
    ).count_variable(
        contrasts=[stratum_column, "species_id", "sex", "length_bin"],
        variable="length_count",
        fun="sum",
    )

    # Return output
    return {
        "binned_aged_counts_df": aged_number_distribution,
        "binned_aged_counts_filtered_df": aged_number_distribution_filtered,
        "binned_unaged_counts_df": unaged_number_distribution,
    }


def number_proportions(count_dict: dict) -> dict:
    """
    Calculate the number/count proportions of aged and unaged fish per stratum.

    Parameters
    ----------
    count_dict: dict
        Dictionary containing multiple dataframes with aged and unaged quantized/binned counts.
    """

    # Get the name of the stratum column
    stratum_col = [
        col for col in count_dict["binned_aged_counts_df"].columns if "stratum" in col.lower()
    ][0]

    # Calculate total numbers among aged samples
    # ---- Collect unique strata
    strata_unique = pd.DataFrame(
        {
            f"{stratum_col}": np.unique(
                np.concatenate(
                    [
                        count_dict["binned_aged_counts_df"][stratum_col],
                        count_dict["binned_unaged_counts_df"][stratum_col],
                    ]
                )
            ),
        },
    )
    # ---- Collect unique sex
    sex_unique = pd.DataFrame(
        {
            "sex": np.unique(
                np.concatenate(
                    [
                        count_dict["binned_aged_counts_df"].sex,
                        count_dict["binned_unaged_counts_df"].sex,
                    ]
                )
            ),
        },
    )
    # ---- Collect unique species id
    species_unique = pd.DataFrame(
        {
            "species_id": np.unique(
                np.concatenate(
                    [
                        count_dict["binned_aged_counts_df"].species_id,
                        count_dict["binned_unaged_counts_df"].species_id,
                    ]
                )
            ),
        },
    )
    # ---- Initialize dataframe
    count_total = (
        strata_unique.merge(sex_unique, how="cross")
        .merge(species_unique, how="cross")
        .set_index([stratum_col, "species_id", "sex"])
    )
    # ---- Aged (overall)
    count_total["total_overall_aged"] = (
        count_dict["binned_aged_counts_df"]
        .groupby([stratum_col, "species_id", "sex"])["count"]
        .sum()
    )
    # ---- Aged (filtered)
    count_total["total_filtered_aged"] = (
        count_dict["binned_aged_counts_filtered_df"]
        .groupby([stratum_col, "species_id", "sex"])["count"]
        .sum()
    )
    # ---- Unaged
    count_total["total_overall_unaged"] = (
        count_dict["binned_unaged_counts_df"]
        .groupby([stratum_col, "species_id", "sex"])["count"]
        .sum()
    )
    # ---- Fill NaN
    count_total.fillna(0, inplace=True)
    count_total = count_total.reset_index().set_index(stratum_col)
    # ---- Grand totals
    count_total["total_overall"] = (
        count_total[count_total.sex == "all"].total_filtered_aged
        + count_total[count_total.sex == "all"].total_overall_unaged
    )
    count_total = count_total.reset_index()

    # Calculate number proportions
    # ---- Aged (number distributed over age and length)
    aged_number_proportion = count_dict["binned_aged_counts_filtered_df"][
        count_dict["binned_aged_counts_filtered_df"].sex.isin(["male", "female", "all"])
    ].merge(
        count_total[[stratum_col, "species_id", "sex", "total_filtered_aged", "total_overall"]],
        on=[stratum_col, "species_id", "sex"],
    )
    # -------- Aged-specific proportion
    aged_number_proportion["proportion_number_aged"] = (
        aged_number_proportion["count"] / aged_number_proportion["total_filtered_aged"]
    )
    # -------- Overall proportion
    aged_number_proportion["proportion_number_overall_aged"] = (
        aged_number_proportion["count"] / aged_number_proportion["total_overall"]
    )
    # -------- Gather aged (sexed) number proportions
    sex_number_proportions = (
        aged_number_proportion.groupby([stratum_col, "species_id", "sex"], observed=False)[
            "proportion_number_overall_aged"
        ]
        .sum()
        .reset_index()
    )
    # ---- Unaged (number distributed over length)
    unaged_number_proportion = count_dict["binned_unaged_counts_df"].merge(
        count_total[[stratum_col, "species_id", "sex", "total_overall_unaged", "total_overall"]],
        on=[stratum_col, "species_id", "sex"],
    )
    # -------- Unaged-specific proportion
    unaged_number_proportion["proportion_number_unaged"] = (
        unaged_number_proportion["count"] / unaged_number_proportion["total_overall_unaged"]
    )
    # -------- Overall proportion
    unaged_number_proportion["proportion_number_overall_unaged"] = (
        unaged_number_proportion["count"] / unaged_number_proportion["total_overall"]
    )
    # ---- Gather unaged (sexed) number proportions
    # -------- Merge
    sex_number_proportions = sex_number_proportions.merge(
        unaged_number_proportion.groupby([stratum_col, "species_id", "sex"])[
            "proportion_number_overall_unaged"
        ]
        .sum()
        .reset_index(),
        how="outer",
    ).fillna(0.0)
    # -------- Sum overall total across aged and unaged samples
    sex_number_proportions["proportion_number_overall"] = (
        sex_number_proportions.proportion_number_overall_aged
        + sex_number_proportions.proportion_number_overall_unaged
    )

    # Calculate overall number proportions across age
    age_number_proportions = (
        aged_number_proportion.groupby([stratum_col, "species_id", "age_bin"], observed=False)[
            "proportion_number_aged"
        ]
        .sum()
        .reset_index(name="proportion_number")
    )

    # Return output
    return {
        "age_proportions_df": age_number_proportions,
        "sex_proportions_df": sex_number_proportions,
        "aged_length_proportions_df": aged_number_proportion,
        "unaged_length_proportions_df": unaged_number_proportion,
    }


def fit_length_weights(proportions_dict: dict, length_weight_dict: dict) -> pd.DataFrame:
    """
    Calculate the weight proportion for each length-bin across all and sexed fish

    Parameters
    ----------
    proportions_dict: dict
        Dictionary containing multiple dataframes with aged and unaged quantized/binned proportions.
    length_weight_dict: dict
        Dictionary containing length-weight regression terms and fitted values.
    """

    aged_proportions = proportions_dict["aged_length_proportions_df"]
    unaged_proportions = proportions_dict["unaged_length_proportions_df"]
    sex_proportions = proportions_dict["sex_proportions_df"]

    fitted_weight = length_weight_dict["length_weight_regression"]["weight_fitted_df"]

    # Get the name of the stratum column
    stratum_col = [col for col in aged_proportions.columns if "stratum" in col.lower()][0]

    # Sum number proportions of aged specimens per stratum
    aged_unaged_proportions = (
        aged_proportions[aged_proportions.sex == "all"]
        .groupby([stratum_col])["proportion_number_overall_aged"]
        .sum()
        .reset_index(name="number_proportion_aged")
    )

    # Calculate unaged proportions per stratum
    aged_unaged_proportions["number_proportion_unaged"] = (
        1.0 - aged_unaged_proportions["number_proportion_aged"]
    )

    # Calculate the mixed aged and unaged number proportions
    # ---- Merge aged and unaged number proportions
    stratum_proportions_sexed = aged_unaged_proportions.merge(sex_proportions, on=[stratum_col])
    # ---- Calculate unaged number proportions per sex per stratum
    stratum_proportions_sexed["proportion_unaged"] = (
        stratum_proportions_sexed.number_proportion_unaged
        / (
            stratum_proportions_sexed.number_proportion_unaged
            + stratum_proportions_sexed.proportion_number_overall_aged
        )
    )
    # ---- Calculate aged number proportions per sex per stratum
    stratum_proportions_sexed["proportion_aged"] = stratum_proportions_sexed[
        "proportion_number_overall_aged"
    ] / (
        stratum_proportions_sexed["proportion_number_overall_aged"]
        + stratum_proportions_sexed["proportion_unaged"]
    )
    # ---- Reduce columns and ensure sex is in 'male/female/all'
    stratum_proportions_sexed = stratum_proportions_sexed[
        stratum_proportions_sexed.sex != "unsexed"
    ][[stratum_col, "sex", "proportion_aged", "proportion_unaged"]]

    # Combine the aged-unaged (or station-specific) proportions for calculations
    # ---- Wide-to-long DataFrame
    station_proportions = pd.wide_to_long(
        stratum_proportions_sexed,
        stubnames="proportion",
        i=[stratum_col, "sex"],
        j="group",
        sep="_",
        suffix="\\w+",
    ).reset_index()
    # ---- Convert to Table (to replicate indexed matrix operations)
    station_proportions_table = station_proportions.pivot_table(
        index=["group", "sex"], columns=[stratum_col], values="proportion"
    ).fillna(0.0)

    # Calculate the number length proportions that will be later converted into weight
    # ---- Aged length bins
    aged_length_distribution = (
        aged_proportions.groupby([stratum_col, "sex", "length_bin"], observed=False)[
            "proportion_number_aged"
        ]
        .sum()
        .reset_index(name="number_proportion")
    )
    # ---- Unaged length bins
    unaged_length_distribution = unaged_proportions[unaged_proportions.sex != "unsexed"][
        [stratum_col, "sex", "length_bin", "proportion_number_unaged"]
    ].rename(columns={"proportion_number_unaged": "number_proportion"})
    # ---- Concatenate the two datasets
    length_number_proportions = pd.concat(
        [
            aged_length_distribution.assign(group="aged"),
            unaged_length_distribution.assign(group="unaged"),
        ]
    )
    # ---- Convert to Table (to replicate indexed matrix operations)
    length_proportions_table = length_number_proportions.pivot_table(
        index=["group", "sex", "length_bin"],
        columns=[stratum_col],
        values="number_proportion",
        observed=False,
    ).fillna(0.0)

    # Convert the fitteed weights into a Table (to replicate index matrix operations)
    fitted_weight_table = fitted_weight.pivot_table(
        index=["sex", "length_intervals"], values="weight_fitted", observed=False
    )

    # Calculate the average weights for male, female, and all fish within each stratum
    # ---- All
    weight_all = fitted_weight_table.loc["all"]["weight_fitted"].values.dot(
        length_proportions_table.loc["aged", "all"] * station_proportions_table.loc["aged", "all"]
        + length_proportions_table.loc["unaged", "all"]
        * station_proportions_table.loc["unaged", "all"]
    )
    # ---- Male (Note: the modeled weight calculated for all fish is used instead of the
    # ---- male-specific values)
    weight_male = fitted_weight_table.loc["all"]["weight_fitted"].values.dot(
        length_proportions_table.loc["aged", "male"] * station_proportions_table.loc["aged", "male"]
        + length_proportions_table.loc["unaged", "male"]
        * station_proportions_table.loc["unaged", "male"]
    )
    # ---- Female (Note: the modeled weight calculated for all fish is used instead of the
    # ---- female-specific values)
    weight_female = fitted_weight_table.loc["all"]["weight_fitted"].values.dot(
        length_proportions_table.loc["aged", "female"]
        * station_proportions_table.loc["aged", "female"]
        + length_proportions_table.loc["unaged", "female"]
        * station_proportions_table.loc["unaged", "female"]
    )
    # ---- Combine the stratum-averaged weights for each sex and all fish
    fitted_weight_df = pd.DataFrame(
        {
            f"{stratum_col}": np.tile(
                np.unique(station_proportions[stratum_col]), len(np.unique(station_proportions.sex))
            ),
            "sex": np.repeat(
                ["all", "male", "female"], len(np.unique(station_proportions[stratum_col]))
            ),
            "average_weight": np.concatenate([weight_all, weight_male, weight_female]),
        }
    )

    # Return output
    return fitted_weight_df


def quantize_weights(
    specimen_data: pd.DataFrame,
    length_data: pd.DataFrame,
    length_weight_df: pd.DataFrame,
    stratum_column: str,
) -> dict:
    """
    Quantize the weight of animals belonging to each binned length and age

    Parameters
    ----------
    specimen_data: pd.DataFrame
        Dataframe containing aged length-weight data.
    length_data: pd.DataFrame
        Dataframe containing unaged length data.
    length_weight_df: pd.DataFrame
        Dataframe containing the fitted weights per binned length value
    stratum_column: str
        Stratum column name.
    """

    # Generate sex-specific interpolators for fitted length-weight values for unaged fish
    # (station 1)
    # ---- Parse the male- and female-specific fitted weight values
    length_weight_sex = length_weight_df.copy()[length_weight_df["sex"].isin(["male", "female"])]
    # ---- Extract 'length' from the interval categories
    length_weight_sex.loc[:, "length"] = length_weight_sex.loc[:, "length_intervals"].apply(
        lambda x: x.mid
    )
    # ---- Create interpolator functions
    interpolators = group_interpolator_creator(
        grouped_data=length_weight_sex,
        independent_var="length",
        dependent_var="weight_fitted",
        contrast="sex",
    )

    # ---- Create helper/lambda function
    def weight_interpolator(dataframe_row):
        sex = dataframe_row["sex"]
        length = dataframe_row["length"]
        if sex in interpolators:
            return interpolators[sex](length)
        else:
            return None

    # ---- Extract only sexed fish from the unaged (station 1) length dataset
    length_data_sexed = length_data[length_data["sex"].isin(["male", "female"])].copy()
    # ---- Add interpolated weights to the general length dataset
    length_data_sexed.loc[:, "weight_interp"] = (
        length_data_sexed.apply(weight_interpolator, axis=1) * length_data_sexed["length_count"]
    )
    # ---- Convert interpolated weights (summed across length counts) into a table
    length_table_sexed = length_data_sexed.pivot_table(
        columns=[stratum_column, "sex"],
        index=["length_bin"],
        values="weight_interp",
        aggfunc="sum",
        observed=False,
    )

    # Remove specimen data with missing data required for this analysis
    # ---- Drop unsexed fish
    specimen_data_filtered = specimen_data[specimen_data.group_sex != "unsexed"]
    # ---- Remove NaN
    specimen_data_filtered = specimen_data_filtered.dropna(subset=["length", "weight", "age"])
    # ---- Convert to a table
    specimen_table_sexed = specimen_data_filtered.pivot_table(
        columns=[stratum_column, "sex", "age_bin"],
        index=["length_bin"],
        values="weight",
        aggfunc="sum",
        observed=False,
    )

    # Return a dictionary of the quantized weights
    return {
        "aged_length_weight_tbl": specimen_table_sexed,
        "unaged_length_weight_tbl": length_table_sexed,
    }


def weight_proportions(
    catch_data: pd.DataFrame,
    proportions_dict: dict,
    length_weight_df: pd.DataFrame,
    distributions_dict: dict,
    stratum_column: str,
):
    """
    Calculate the weight proportions of aged and unaged animals across length and age bins

    Parameters
    ----------
    catch_data: pd.DataFrame
        Dataframe containing unaged weight data.
    proportions_dict: dict
        Dictionary containing aged and unaged number proportions.
    length_weight_df: pd.DataFrame
        Dataframe containing fitted weights per length bin.
    distributions_dict: dict
        Dictionary containing length-weight distributions.
    stratum_column: str
        Stratum column name.

    Notes
    -----
    This function produces the proportion of male and female, and the average weight of male,
    female, and total (male, female, and unsexed fish). The average weight is estimated using the
    length-weight relationship fitted in ``fit_binned_length_weight_relationship``.
    """

    # Calculate the sexed and total stratum weights for each sex among aged fish
    # ---- Extract the aged/specimen quantized weights
    aged_weights_binned = distributions_dict["aged_length_weight_tbl"].copy()
    # ---- Sum these weights for each sex (male/female)
    aged_weights_sex = aged_weights_binned.sum().unstack(["age_bin"]).sum(axis=1).unstack(0)
    # ---- Calculate the stratum totals
    aged_strata_weights = aged_weights_sex.sum().reset_index(name="stratum_weight")

    # Calculate the sexed and total stratum weights for each sex among unaged fish
    # ---- Sum the net haul weights from station 1/unaged fish
    catch_strata_weights = catch_data.count_variable(
        contrasts=[stratum_column], variable="haul_weight", fun="sum"
    )
    # ---- Rename resulting columns for both
    catch_strata_weights.rename(columns={"count": "stratum_weight"}, inplace=True)

    # Sum the sexed and total weights from the weight-fitted unaged data
    # ---- Extract the unaged/length quantized weights
    unaged_weights_binned = distributions_dict["unaged_length_weight_tbl"].copy()
    # ---- Calculate the total weight per stratum per sex
    unaged_weights_sex = unaged_weights_binned.sum()
    # ---- Calculate the stratum totals
    unaged_strata_weights = unaged_weights_sex.unstack(0).sum(axis=0)
    # ---- Standardize the unaged sexed weights
    unaged_weights_sex_standardized = (unaged_weights_sex / unaged_strata_weights).unstack(
        0
    ) * catch_strata_weights["stratum_weight"].to_numpy()

    # Calculate the specimen (aged) weight proportions
    # ---- Re-pivot the aged weight bins table
    aged_weights_binned_pvt = (
        aged_weights_binned.unstack()
        .reset_index(name="weight")
        .pivot_table(
            columns=[stratum_column],
            index=["age_bin", "length_bin", "sex"],
            values="weight",
            observed=False,
        )
    )
    # ---- Divide by the aged stratum weights (relative to only aged fish)
    aged_weight_proportions_pvt = (
        aged_weights_binned_pvt / aged_strata_weights["stratum_weight"].to_numpy()
    )
    # ---- Pivot back to the desired format
    aged_weight_proportions = (
        aged_weight_proportions_pvt.stack()
        .reset_index(name="weight_proportion")
        .pivot_table(
            columns=[stratum_column, "sex", "age_bin"],
            index="length_bin",
            values="weight_proportion",
            observed=False,
        )
    )
    # ---- Calculate the internal (i.e. only aged fish) for each sex
    within_aged_sex_proportions = aged_weight_proportions.sum().unstack("age_bin").sum(axis=1)

    # Calculate the total strata weights
    total_strata_weights = pd.concat([aged_strata_weights, catch_strata_weights]).pivot_table(
        columns=[stratum_column], aggfunc="sum", values="stratum_weight", observed=False
    )

    # Calculate the weight proportions relative to the overall stratum weights
    # ---- Aged
    # -------- Reformat into dataframe and merge with total stratum weights
    aged_weights_binned_df = (
        aged_weights_binned_pvt.stack()
        .to_frame("specimen_weight")
        .reset_index()
        .merge(total_strata_weights.T.reset_index(), on=stratum_column)
    )
    # -------- Calculate proportions
    aged_weights_binned_df["weight_proportion_overall"] = (
        aged_weights_binned_df["specimen_weight"] / aged_weights_binned_df["stratum_weight"]
    )
    # -------- Consolidate to calculate the sexed proportions per stratum
    aged_weight_sex_proportions = aged_weights_binned_df.groupby([stratum_column, "sex"])[
        "weight_proportion_overall"
    ].sum()
    # ---- Unaged
    # -------- Reformat into dataframe and merge with total stratum weights
    unaged_weights_sex_standardized_df = (
        unaged_weights_sex_standardized.stack()
        .to_frame("catch_weight")
        .reset_index()
        .merge(total_strata_weights.T.reset_index(), on=stratum_column)
    )
    # -------- Calculate proportions
    unaged_weights_sex_standardized_df["weight_proportion_overall"] = (
        unaged_weights_sex_standardized_df["catch_weight"]
        / unaged_weights_sex_standardized_df["stratum_weight"]
    )
    # -------- Back-calculate the sexed weight proportions relative to just unaged fish
    # ------------ Aggregate proportions
    unaged_total_sex_proportions = unaged_weights_sex_standardized_df.pivot_table(
        columns=["sex"], index=[stratum_column], values="weight_proportion_overall"
    ).sum(axis=1)
    # ------------ Re-compute the proportions
    unaged_weight_sex_proportions = (
        unaged_weights_sex_standardized_df.pivot_table(
            index=["sex"], columns=[stratum_column], values="weight_proportion_overall"
        )
        / unaged_total_sex_proportions.to_numpy()
    )

    # Compute the overall length-binned weight distributions among unaged fish
    # ---- Extract the fitted weight values calculated for all fish
    length_weight_all = length_weight_df[length_weight_df["sex"] == "all"]
    # ---- Generate the fitted weight array
    fitted_weights = length_weight_all["weight_fitted"].to_numpy()
    # ---- Extract the number proportions computed for unaged fish
    unaged_number_proportions = proportions_dict["unaged_length_proportions_df"]
    # ---- Filter out values besides those computed for 'all' fish
    unaged_number_proportions = unaged_number_proportions[unaged_number_proportions["sex"] == "all"]
    # ---- Convert to a table
    unaged_number_proportions_tbl = unaged_number_proportions.pivot_table(
        columns=[stratum_column],
        index=["length_bin"],
        values="proportion_number_unaged",
        aggfunc="sum",
        observed=False,
    )
    # ---- Apportion the averaged weights
    unaged_apportioned_weights = unaged_number_proportions_tbl.T * fitted_weights
    # ---- Compute the average weight proportions per length bin per stratum
    unaged_length_weights = unaged_apportioned_weights.T / unaged_apportioned_weights.sum(axis=1)
    # ---- Convert back to a DataFrame
    unaged_weight_proportions_df = unaged_length_weights.unstack().reset_index(
        name="weight_proportion"
    )

    # Calculate the aged and unaged weight proportions
    # ---- Aged
    aged_proportions = aged_weight_sex_proportions.unstack("sex").sum(axis=1)
    # ---- Unaged
    unaged_proportions = 1 - aged_proportions
    # -------- Re-weight the unaged sexed proportions
    unaged_weight_sex_proportions_overall = (
        (unaged_weight_sex_proportions * unaged_proportions).astype(float).fillna(0.0)
    )

    # Format the outputs
    # ---- Aged: stratum-sex-age-length relative to aged and total weights
    aged_overall_df = (
        aged_weight_proportions.unstack()
        .reset_index(name="weight_proportions")
        .merge(
            aged_weights_binned_df[
                [stratum_column, "age_bin", "length_bin", "sex", "weight_proportion_overall"]
            ]
        )
    )
    # ---- Aged: stratum-sex relative to total weights
    aged_sex_df = within_aged_sex_proportions.reset_index(name="weight_proportion_aged").set_index(
        [stratum_column, "sex"]
    )
    # ---- Add the aged sex proportiosn relative to the overall survey
    aged_sex_df["weight_proportion_overall_aged"] = aged_weight_sex_proportions
    # ---- Consolidate the aged and unaged sexed dataframes
    # -------- Initialize the dataframe
    aged_unaged_sex_proportions = aged_sex_df
    # --------- Add the within-unaged weight proportions
    aged_unaged_sex_proportions["weight_proportion_unaged"] = (
        unaged_weight_sex_proportions.unstack()
    )
    # --------- Add the overall-unaged weight proportions
    aged_unaged_sex_proportions["weight_proportion_overall_unaged"] = (
        unaged_weight_sex_proportions_overall.unstack()
    )
    # ---- Overall aged and unaged proportions
    aged_unaged_proportions = aged_proportions.to_frame(
        "aged_proportions"
    )  # .reset_index(name="aged_proportions")
    # -------- Add unaged proportions
    aged_unaged_proportions["unaged_proportions"] = unaged_proportions

    # Return output
    return {
        "aged_weight_proportions_df": aged_overall_df,
        "unaged_weight_proportions_df": unaged_weight_proportions_df,
        "aged_unaged_sex_weight_proportions_df": (
            aged_unaged_sex_proportions.astype(float).reset_index().fillna(0.0)
        ),
        "aged_unaged_weight_proportions_df": aged_unaged_proportions.reset_index(),
    }


def age1_metric_proportions(
    distributions_dict: dict, proportions_dict: dict, TS_L_parameters: dict, settings_dict: dict
):
    """
    Calculate the age-1 number, weight, and NASC proportions for each stratum

    Parameters
    ----------
    distributions_dict: dict
        Dictionary containing length-weight distributions.
    proportions_dict: dict
        Dictionary containing number and weight proportions.
    TS_L_parameters: dict
        Dictionary containing the TS-length regression parameters.
    settings_dict: dict
        Dictionary that contains all of the analysis settings that detail specific algorithm
        arguments and user-defined inputs.
    """

    # Get stratum column name
    stratum_col = settings_dict["transect"]["stratum_name"]

    # Calculate the age1 number proportion
    # ---- Initialize the dataframe
    age_proportions = proportions_dict["number"]["aged_length_proportions_df"].copy()
    # ---- Only consider 'all' fish
    age_proportions = age_proportions[
        (age_proportions["sex"] == "all") & (age_proportions[stratum_col] != 0)
    ].reset_index()
    # ---- Convert to center of length bin
    age_proportions.loc[:, "length_mid"] = (
        age_proportions.loc[:, "length_bin"].apply(lambda df: df.mid).astype(float)
    )
    # ---- Convert into a pivot table
    age_proportions_table = age_proportions.pivot_table(
        index=["length_bin"],
        columns=[stratum_col, "age_bin"],
        values="proportion_number_aged",
        aggfunc="sum",
        observed=False,
    )
    # ---- Sum the number proportions for each age bin within each stratum
    age1_proportions = age_proportions_table.sum()[:, 1].to_numpy()

    # Calculate the new length-averaged sigma_bs for each stratum
    # ---- Extract the length-binned values
    length_bins = distributions_dict["length_bins_df"].copy()
    # ---- Square the length values
    length_bins["length_sq"] = length_bins["length_bins"] ** 2.0
    # ---- Multiply by the TS-length regression coefficient (in the linear domain)
    length_bins["length_sq"] = length_bins["length_sq"] * 10 ** (
        TS_L_parameters["TS_L_intercept"] / 10.0
    )
    # ---- Repivot the number proportion data
    age_proportions_alt_table = age_proportions.pivot_table(
        index=["length_bin"],
        columns=[stratum_col],
        values="proportion_number_aged",
        aggfunc="sum",
        observed=False,
    )
    # ---- Dot product to calculate the new average sigma_bs for all ages
    updated_sigma_bs = length_bins["length_sq"].values.dot(age_proportions_alt_table)

    #
    # ---- Filter out adult (age-2+ fish)
    age_proportions_age1_table = age_proportions[
        age_proportions["age_bin"] == pd.Interval(left=0.5, right=1.5)
    ]
    # ---- Repivot for just age-1 fish
    age_proportions_age1_table = age_proportions_age1_table.pivot_table(
        index=["length_bin"],
        columns=[stratum_col],
        values="proportion_number_aged",
        aggfunc="sum",
        observed=False,
    )
    # ---- Dot product to calculate the average sigma_bs for age-1 fish
    age1_sigma_bs = length_bins["length_sq"].values.dot(age_proportions_age1_table)
    # ---- Calculate age-1 NASC proportioon per stratum
    age1_nasc_proportions = age1_sigma_bs / updated_sigma_bs

    unage_proportions = proportions_dict["number"]["unaged_length_proportions_df"]
    # ---- Only consider 'all' fish
    unage_proportions = unage_proportions[unage_proportions["sex"] == "all"].reset_index()
    # ---- Convert into a pivot table
    unage_proportions_table = unage_proportions.pivot_table(
        columns=[stratum_col],
        index=["length_bin"],
        values="proportion_number_unaged",
        aggfunc="sum",
        observed=False,
    )

    min_index = np.where(length_bins["length_bins"] == 10.0)[0]
    if len(min_index) == 0:
        min_index = 0
    else:
        min_index = min_index[0]
    max_index = length_bins["length_bins"].size

    # Calculate thresholds derived from the summed length distributions of age-1 fish
    # ---- General length distribution
    age1_length_distribution_threshold = (
        unage_proportions_table.iloc[np.arange(min_index, max_index), :]
        * age_proportions_age1_table.iloc[np.arange(min_index, max_index), :]
    ).sum()

    # ---- Just aged length distribution (age-1)
    age1_specific_length_distribution_threshold = age_proportions_age1_table.sum(axis=0)

    age_weight_proportions = proportions_dict["weight"]["aged_weight_proportions_df"]
    age_weight_proportions = age_weight_proportions[age_weight_proportions[stratum_col] != 0]

    age_weight_proportions_table = age_weight_proportions.pivot_table(
        index=["length_bin"],
        columns=["age_bin", stratum_col],
        values="weight_proportions",
        aggfunc="sum",
        observed=False,
    )

    age_weight_proportions_repivot = age_weight_proportions.pivot_table(
        index=["age_bin"],
        columns=[stratum_col],
        values="weight_proportions",
        aggfunc="sum",
        observed=False,
    )

    age1_weight_proportions = np.where(
        (age1_length_distribution_threshold <= 1e-10)
        & (age1_specific_length_distribution_threshold <= 1e-10),
        0.0,
        age_weight_proportions_table[1].sum() / age_weight_proportions_repivot.sum(),
    )

    # Return output
    # ---- Create DataFrame
    apportioned_age1 = pd.DataFrame({f"{stratum_col}": np.unique(age_proportions[stratum_col])})
    # ---- Number proportions
    apportioned_age1["number_proportion"] = age1_proportions
    # ---- Weight proportions
    apportioned_age1["weight_proportion"] = age1_weight_proportions
    # ---- NASC
    apportioned_age1["nasc_proportion"] = age1_nasc_proportions
    # ---- Return
    return apportioned_age1


def distribute_length_age(
    nasc_biology_df: pd.DataFrame, proportions_dict: dict, settings_dict: dict
):
    """
    Distribute population estimates from transect data over length- and age-bins

    Parameters
    ----------
    nasc_to_biology: pd.DataFrame
        Dataframe containing integrated population estimates (e.g. abundance, biomass) at
        georeferenced locations along each transect.
    proportions_dict: dict
        Dictionary containing number and weight proportions.
    settings_dict: dict
        Dictionary that contains all of the analysis settings that detail specific algorithm
        arguments and user-defined inputs.
    """

    # Get the name of the stratum column
    stratum_col = settings_dict["transect"]["stratum_name"]

    # Extract the correct number proportions
    # ---- Unaged, length (Station 1)
    unaged_number_proportions = proportions_dict["number"]["unaged_length_proportions_df"]
    # -------- Drop unusexed sex categories
    unaged_number_proportions = unaged_number_proportions[
        unaged_number_proportions.sex != "unsexed"
    ]
    # ---- Aged, length (Station 2)
    aged_number_proportions = proportions_dict["number"]["aged_length_proportions_df"]
    # -------- Drop unusexed sex categories
    aged_number_proportions = aged_number_proportions[aged_number_proportions.sex != "unsexed"]

    # Extract the correct number proportions
    # ---- Aged, length (Station 2)
    aged_weight_proportions = proportions_dict["weight"]["aged_weight_proportions_df"]
    # -------- Sum to create a total/complete key
    aged_weight_proportions_all = (
        aged_weight_proportions.groupby([stratum_col, "length_bin", "age_bin"], observed=False)[
            "weight_proportions"
        ]
        .sum()
        .reset_index()
    )
    # ---- Concatenate with the full dataset
    aged_weight_proportions = pd.concat(
        [
            aged_weight_proportions.drop("weight_proportion_overall", axis=1),
            aged_weight_proportions_all,
        ]
    )

    # Apportion biomass by sex, length, and age bins
    nasc_abundance = nasc_biology_df[
        [stratum_col, "transect_num", "longitude", "latitude", "abundance"]
    ]
    # ---- Sum the abundance for each stratum
    abundance_strata = nasc_abundance.groupby([stratum_col])["abundance"].sum()
    # ---- Initialize apportioned unaged abundance
    unaged_apportioned_abundance = unaged_number_proportions.set_index([stratum_col])
    # ---- Merge with the grouped sex proportions for each stratum
    unaged_apportioned_abundance["abundance_total"] = abundance_strata
    # ---- Sexed abundance for unaged fish
    unaged_apportioned_abundance["abundance_unaged"] = (
        unaged_apportioned_abundance["abundance_total"]
        * unaged_apportioned_abundance["proportion_number_overall_unaged"]
    ).fillna(0.0)
    # ---- Drop unused columns
    unaged_apportioned_abundance = unaged_apportioned_abundance[
        ["sex", "length_bin", "abundance_unaged"]
    ].reset_index()
    # ---- Convert to pivot table
    unaged_apportioned_abundance_tbl = unaged_apportioned_abundance.pivot_table(
        index=["sex", "length_bin"],
        columns=[stratum_col],
        values="abundance_unaged",
        aggfunc="sum",
        observed=False,
    )
    # ---- Initialize apportioned aged abundance
    aged_apportioned_abundance = aged_number_proportions.set_index([stratum_col])
    # ---- Merge with the grouped sex proportions for each stratum
    aged_apportioned_abundance["abundance_total"] = abundance_strata
    # ---- Sexed abundance for aged fish
    aged_apportioned_abundance["abundance_aged"] = (
        aged_apportioned_abundance["abundance_total"]
        * aged_apportioned_abundance["proportion_number_overall_aged"]
    ).fillna(0.0)
    # ---- Drop unused columns
    aged_apportioned_abundance = aged_apportioned_abundance[
        ["sex", "length_bin", "age_bin", "abundance_aged"]
    ].reset_index()
    # ---- Convert to pivot table
    aged_apportioned_abundance_tbl = aged_apportioned_abundance.pivot_table(
        index=["sex", "length_bin"],
        columns=[stratum_col, "age_bin"],
        values="abundance_aged",
        aggfunc="sum",
        observed=False,
    )

    # Apportion abundance by sex, length, and age bins
    # ---- Extract abundance-specific variable
    nasc_biomass = nasc_biology_df[
        [
            stratum_col,
            "transect_num",
            "longitude",
            "latitude",
            "biomass",
            "biomass_female",
            "biomass_male",
        ]
    ].copy()
    # -------- Adjust column name
    nasc_biomass.rename(columns={"biomass": "biomass_all"}, inplace=True)
    # -------- Pivot from wide to long
    nasc_biomass = pd.wide_to_long(
        nasc_biomass,
        stubnames="biomass",
        i=[stratum_col, "transect_num", "longitude", "latitude"],
        j="sex",
        sep="_",
        suffix=r"\w+",
    ).reset_index()
    # ---- Sum the abundance for each stratum
    biomass_strata = nasc_biomass.groupby([stratum_col, "sex"])["biomass"].sum()
    # -------- Reset the index
    biomass_strata = biomass_strata.reset_index()
    # ---- Initialize apportioned aged biomass
    aged_apportioned_biomass = aged_weight_proportions_all.merge(biomass_strata, on=[stratum_col])
    # ---- Sexed abundance for unaged fish
    aged_apportioned_biomass["biomass_aged"] = (
        aged_apportioned_biomass["biomass"] * aged_apportioned_biomass["weight_proportions"]
    ).fillna(0.0)
    # ---- Drop unused columns
    aged_apportioned_biomass = aged_apportioned_biomass[
        [stratum_col, "sex", "length_bin", "age_bin", "biomass_aged"]
    ]
    # ---- Convert to pivot table
    aged_apportioned_biomass_tbl = aged_apportioned_biomass.pivot_table(
        index=["sex", "length_bin"],
        columns=[stratum_col, "age_bin"],
        values="biomass_aged",
        aggfunc="sum",
        observed=False,
    )

    # Return outputs
    return {
        "abundance": {
            "aged_abundance_df": aged_apportioned_abundance_tbl,
            "unaged_abundance_df": unaged_apportioned_abundance_tbl,
        },
        "biomass": {"aged_biomass_df": aged_apportioned_biomass_tbl},
    }


def partition_transect_age(
    nasc_biology_df: pd.DataFrame,
    fitted_weight_dict: pd.DataFrame,
    settings_dict: dict,
    population_dict: dict,
    strata_adult_proportions_df: pd.DataFrame,
):
    """
    Reapportion population estimates across age- and length-bins to separate age-1 and age-2+ fish,
    estimate age-1 distributions for unaged fish, and generate a summary table

    Parameters
    ----------
    nasc_to_biology: pd.DataFrame
        Dataframe containing integrated population estimates (e.g. abundance, biomass) at
        georeferenced locations along each transect.
    fitted_weight_dict: dict
        Dictionary containing fitted weights for each sex and length-bin.
    settings_dict: dict
        Dictionary that contains all of the analysis settings that detail specific algorithm
        arguments and user-defined inputs.
    population_dict: dict
        Dictionary that contains all of the population-level estimates distributed over length and
        age.
    strata_adult_proportions_df: pd.DataFrame
        Dataframe that includes the relative age-1:age-2+ ratios/proportions for number, weight,
        and NASC.
    """

    # Get the name of the stratum column
    stratum_col = settings_dict["transect"]["stratum_name"]

    # Procedure where age-1 fish were excluded from the acoustic survey biological distributions
    # ---- Merge adult proportions with acoustically derived georeferenced biological data
    adult_data = nasc_biology_df.merge(
        strata_adult_proportions_df, on=[stratum_col], how="left"
    ).fillna(0.0)
    # ---- Adjust the full number density, biomass density, and NASC estimates
    # -------- NASC
    adult_data["nasc"] = adult_data["nasc"] * adult_data["nasc_proportion"]
    # -------- Number density
    adult_data["number_density"] = adult_data["number_density"] * adult_data["number_proportion"]
    adult_data["number_density_female"] = (
        adult_data["number_density_female"] * adult_data["number_proportion"]
    )
    adult_data["number_density_male"] = (
        adult_data["number_density_male"] * adult_data["number_proportion"]
    )
    # -------- Abundance
    adult_data["abundance"] = adult_data["abundance"] * adult_data["number_proportion"]
    adult_data["abundance_female"] = (
        adult_data["abundance_female"] * adult_data["number_proportion"]
    )
    adult_data["abundance_male"] = adult_data["abundance_male"] * adult_data["number_proportion"]
    # -------- Biomass density
    adult_data["biomass_density"] = adult_data["biomass_density"] * adult_data["weight_proportion"]
    adult_data["biomass_density_female"] = (
        adult_data["biomass_density_female"] * adult_data["weight_proportion"]
    )
    adult_data["biomass_density_male"] = (
        adult_data["biomass_density_male"] * adult_data["weight_proportion"]
    )
    # -------- Biomass
    adult_data["biomass"] = adult_data["biomass"] * adult_data["weight_proportion"]
    adult_data["biomass_female"] = adult_data["biomass_female"] * adult_data["weight_proportion"]
    adult_data["biomass_male"] = adult_data["biomass_male"] * adult_data["weight_proportion"]
    # ---- Drop unused column names
    adult_data = adult_data.filter(regex="^(?!.*(_proportion|_unsexed))")

    # Adjust the population abundance tables to include only age-1 fish
    # ---- Extract abundances distributed for unaged lengths
    abundance_unaged_length = population_dict["tables"]["abundance"]["unaged_abundance_df"]
    # ---- Convert `strata_adult_proportions_df` into a similarly indexed table
    strata_adult_proportions_table = strata_adult_proportions_df.pivot_table(index=stratum_col).T
    # ---- Convert the table to represent age-1 proportions
    strata_age1_proportions_table = 1.0 - strata_adult_proportions_table
    # ---- Distribute the age-1 proportions across the unaged abundances
    abundance_unaged_age1_tbl = (
        strata_age1_proportions_table.loc["number_proportion"] * abundance_unaged_length
    ).fillna(0.0)

    fitted_weight = fitted_weight_dict["length_weight_regression"]["weight_fitted_df"]

    # ---- Extract abundances distributed for unaged lengths
    abundance_aged_length = population_dict["tables"]["abundance"]["aged_abundance_df"]
    # ---- Reindex
    abundance_age1_length = (
        abundance_aged_length.T.reset_index().set_index(["age_bin", stratum_col]).loc[1].T
    )
    # ---- Calculate the summed biomass across all strata for age-1 fish
    # -------- All fish
    fitted_biomass_all = (
        fitted_weight[fitted_weight.sex == "all"]
        .drop("sex", axis=1)["weight_fitted"]
        .values.dot(abundance_age1_length.loc["all", :])
        .sum()
    )
    # -------- Female fish
    fitted_biomass_female = (
        fitted_weight[fitted_weight.sex == "all"]
        .drop("sex", axis=1)["weight_fitted"]
        .values.dot(abundance_age1_length.loc["female", :])
        .sum()
    )
    # -------- Male fish
    fitted_biomass_male = (
        fitted_weight[fitted_weight.sex == "all"]
        .drop("sex", axis=1)["weight_fitted"]
        .values.dot(abundance_age1_length.loc["male", :])
        .sum()
    )
    # ---- Calculate the estimated biomass proportions/contributions
    female_ratio = fitted_biomass_female / fitted_biomass_all
    male_ratio = fitted_biomass_male / fitted_biomass_all
    # ---- Get the age-1 biomass from `population_dict`
    biomass_aged_length = population_dict["tables"]["biomass"]["aged_biomass_df"]
    # ---- Reindex and extract just the age-1 biomass estimates
    biomass_age1_length = (
        biomass_aged_length.T.reset_index().set_index(["age_bin", stratum_col]).loc[1].T
    )
    # ---- Calculate the age-1 biomass among male fish
    # -------- Sum the total age-1 biomass
    biomass_age1_total = biomass_age1_length.loc["all",].sum().sum()
    # -------- Sum the total female age-1 biomass
    biomass_age1_female = biomass_age1_total * female_ratio
    # -------- Sum the total male age-1 biomass
    biomass_age1_male = biomass_age1_total * male_ratio
    # -------- Sum the mixed age-1 biomass
    biomass_age1_mixed = biomass_age1_total - biomass_age1_female - biomass_age1_male

    # Return outputs
    # ---- Convert biomass estimates into a summary table
    # -------- Initialize dataframe
    biomass_summary_df = pd.DataFrame({"sex": ["all", "female", "male", "unsexed", "mixed"]})
    # -------- Calculate biomass estimates for age-1 fish
    biomass_summary_df["biomass_age1"] = np.array(
        [biomass_age1_total, biomass_age1_female, biomass_age1_male, 0.0, biomass_age1_mixed]
    )
    # ---- Biomass for adult fish
    biomass_summary_df["biomass_adult"] = np.array(
        [
            biomass_aged_length.loc["all", :].sum().sum() - biomass_age1_total,
            biomass_aged_length.loc["female", :].sum().sum() - biomass_age1_female,
            biomass_aged_length.loc["male", :].sum().sum() - biomass_age1_male,
            nasc_biology_df["biomass_unsexed"].sum(),
            nasc_biology_df[nasc_biology_df["fraction_hake"] < 1.0]["biomass"].sum()
            - biomass_age1_mixed,
        ]
    )
    # -------- Calculate biomass estimates for all fish
    biomass_summary_df["biomass_all"] = (
        biomass_summary_df["biomass_adult"] + biomass_summary_df["biomass_age1"]
    )
    # ---- Generate outputs
    return adult_data, biomass_summary_df, abundance_unaged_age1_tbl


def impute_kriged_values(
    aged_age_length_table: pd.DataFrame,
    unaged_length_table: pd.DataFrame,
    aged_length_totals: pd.DataFrame,
    unaged_apportioned_table: pd.DataFrame,
    settings_dict: dict,
):
    """
    Impute unaged population estimates over length-bins where there are no corresponding aged
    values.

    Parameters
    ----------
    aged_age_length_table: pd.DataFrame
        Aged population estimates distributed over age- and length-bins.
    fitted_weight_dict: dict
        Unaged population estimates distributed over length-bins.
    aged_length_totals: pd.DataFrame
        Total population estimates for aged fish distributed over just age-bins.
    unaged_apportioned_table: pd.DataFrame
        Dataframe that includes unaged population estimates apportioned over age- and length-bins
        (based on age distributions from aged measurements).
    settings_dict: dict
        Dictionary that contains all of the analysis settings that detail specific algorithm
        arguments and user-defined inputs.
    """
    # Extract the biological variable name (independent of area)
    biology_col = settings_dict["variable"].replace("_density", "")

    # Imputation is required when unaged values are present but aged values are absent at shared
    # length bins! This requires an augmented implementation to address this accordingly
    # ---- Sum across all age bins (of the aged fish data) to generate totals for each row (i.e.
    # ---- length bin)
    summed_aged_length_totals = aged_age_length_table.T.sum()
    # ---- Extract the indices of the summed totals that equal 0.0 for male and female fish
    # -------- Male
    male_zero_aged = np.where(summed_aged_length_totals.loc["male"] == 0.0)[0]
    # -------- Female
    female_zero_aged = np.where(summed_aged_length_totals.loc["female"] == 0.0)[0]
    # ---- Extract the inverse where biological totals are present
    # -------- Male
    male_nonzero_aged = np.where(summed_aged_length_totals.loc["male"] != 0.0)[0]
    # -------- Female
    female_nonzero_aged = np.where(summed_aged_length_totals.loc["female"] != 0.0)[0]
    # ---- Pivot the unaged data and find male and female values that are non-zero
    # -------- Male
    male_nonzero_unaged = unaged_length_table["male"].iloc[male_zero_aged] != 0.0
    # -------- Convert to index
    male_nonzero_unaged_idx = male_zero_aged[male_nonzero_unaged]
    # -------- Female
    female_nonzero_unaged = unaged_length_table["female"].iloc[female_zero_aged] != 0.0
    # -------- Convert to index
    female_nonzero_unaged_idx = female_zero_aged[female_nonzero_unaged]
    # ---- Re-pivot the unaged apportioned values (if necessary)
    if (len(male_nonzero_unaged) > 0) | (len(female_nonzero_unaged)) > 0:
        unaged_values_pvt = (
            unaged_apportioned_table.copy()
            .unstack()
            .reset_index(name="values")
            .pivot_table(
                index=["length_bin"], columns=["sex", "age_bin"], values="values", observed=False
            )
        )
        # ---- Find the closest indices that can be used for nearest-neighbors imputation
        if len(male_nonzero_unaged) > 0:
            # -------- Male
            imputed_male = male_nonzero_aged[
                np.argmin(
                    np.abs(male_zero_aged[male_nonzero_unaged][:, np.newaxis] - male_nonzero_aged),
                    axis=1,
                )
            ]
            # ---- Update the values
            unaged_values_pvt.iloc[
                male_nonzero_unaged_idx, unaged_values_pvt.columns.get_loc("male")
            ] = (
                unaged_length_table["male"].iloc[male_nonzero_unaged_idx].to_numpy()
                * aged_age_length_table.loc["male"].iloc[imputed_male].T
                / aged_length_totals["male"].iloc[imputed_male]
            ).T
        if len(female_nonzero_unaged) > 0:
            # -------- Female
            imputed_female = female_nonzero_aged[
                np.argmin(
                    np.abs(
                        female_zero_aged[female_nonzero_unaged][:, np.newaxis] - female_nonzero_aged
                    ),
                    axis=1,
                )
            ]
            # ---- Update the values
            unaged_values_pvt.iloc[
                female_nonzero_unaged_idx, unaged_values_pvt.columns.get_loc("female")
            ] = (
                unaged_length_table["female"].iloc[female_nonzero_unaged_idx].to_numpy()
                * aged_age_length_table.loc["female"].iloc[imputed_female].T
                / aged_length_totals["female"].iloc[imputed_female]
            ).T
        # ---- Update the original unaged apportioned table
        unaged_apportioned_table = (
            unaged_values_pvt.unstack()
            .reset_index(name="values")
            .pivot_table(
                index=["length_bin"], columns=["age_bin", "sex"], values="values", observed=False
            )
        )
        # ---- Alert message (if verbose = T)
        if settings_dict["verbose"]:
            # ---- Male:
            if len(male_nonzero_unaged) > 0:
                # ---- Get interval values
                intervals_list = [
                    str(interval)
                    for interval in male_nonzero_unaged.index[male_nonzero_unaged].values
                ]
                # ---- Print
                print(
                    f"""Imputed apportioned unaged male {biology_col} at length bins:\n"""
                    f"""{', '.join(intervals_list)}"""
                )
            # ---- Female:
            if len(female_nonzero_unaged) > 0:
                # ---- Get interval values
                intervals_list = [
                    str(interval)
                    for interval in female_nonzero_unaged.index[female_nonzero_unaged].values
                ]
                # ---- Print
                print(
                    f"""Imputed apportioned unaged female {biology_col} at length bins:\n"""
                    f"""{', '.join(intervals_list)}"""
                )
    # ---- Sum the aged and unaged estimates together
    return (
        (unaged_apportioned_table + aged_age_length_table.unstack("sex"))
        .unstack()
        .reset_index(name=f"{biology_col}_apportioned")
    )


def reallocate_kriged_age1(kriging_table: pd.DataFrame, settings_dict: dict):
    """
    Allocate kriged age-1 population estimates over age-2+ age- and length-bins

    Parameters
    ----------
    kriged_table: pd.DataFrame
        Population estimates distributed over age- and length-bins.
    settings_dict: dict
        Dictionary that contains all of the analysis settings that detail specific algorithm
        arguments and user-defined inputs.
    """

    # Extract the biological variable (independent of area)
    biology_col = settings_dict["variable"].replace("_density", "")

    # Pivot the kriged table
    kriged_tbl = kriging_table.pivot_table(
        index=["length_bin"],
        columns=["sex", "age_bin"],
        values=f"{biology_col}_apportioned",
        observed=False,
        aggfunc="sum",
    )

    # Calculate the aged sums
    # ---- Calculate the age-1 sum
    age_1_sum = kriged_tbl.sum().unstack("sex").iloc[0]
    # ---- Calculate the age-2+ sum
    adult_sum = kriged_tbl.sum().unstack("sex").iloc[1:].sum()

    # Append the aged results to the kriged table
    # ---- Set the index of the kriged table dataframe
    kriging_table.set_index("sex", inplace=True)
    # ---- Append the age-1 sums
    kriging_table["summed_sex_age1"] = age_1_sum
    # ---- Append the adult sums
    kriging_table["summed_sex_adult"] = adult_sum
    # ---- Drop sex as an index
    kriging_table = kriging_table.reset_index()

    # Calculate the new contribution fractions
    # ---- Calculate the adjusted apportionment that will be distributed over the adult values
    kriging_table["adjustment"] = (
        kriging_table["summed_sex_age1"]
        * kriging_table[f"{biology_col}_apportioned"]
        / kriging_table["summed_sex_adult"]
    )
    # ---- Apply the adjustment
    kriging_table.loc[:, f"{biology_col}_apportioned"] = (
        kriging_table.loc[:, f"{biology_col}_apportioned"] + kriging_table.loc[:, "adjustment"]
    )
    # ---- Index by age bins
    kriging_table.set_index("age_bin", inplace=True)
    # ---- Zero out the age-1 values
    kriging_table.loc[[1], f"{biology_col}_apportioned"] = 0.0
    # ---- Remove age as an index
    kriging_table = kriging_table.reset_index()
    # ---- Drop temporary columns
    kriging_table.drop(columns=["summed_sex_age1", "summed_sex_adult", "adjustment"], inplace=True)

    # Return output
    return kriging_table
