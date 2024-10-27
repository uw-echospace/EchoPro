import re
from functools import reduce
from typing import Callable, List, Optional, Union

import numpy as np
import pandas as pd
from scipy import interpolate

from .monkey_patch_dataframe import patch_method_to_DataFrame


@patch_method_to_DataFrame(pd.DataFrame)
def bin_variable(
    dataframe: pd.DataFrame,
    bin_values: Union[np.ndarray, List[np.ndarray]],
    bin_variables: Union[str, List[str]],
):
    """
    Discretizes the target variable into user-defined bins

    Parameters
    ----------
    dataframe: pd.DataFrame
        A DataFrame object containing length and age variables required
        for analyses handling binned variables
    bin_values: np.ndarray
        An array of discrete bin values used to construct the intervals for
        the variable of interest
    bin_variable: str
        The variable that will be binned into discrete intervals
    Notes
    -----
    This will add a column to defined dataframes that groups length and age values
    into each bin that is explicitly defined in the function arguments
    """

    # Convert bin_variable to list if string
    if isinstance(bin_variables, str):
        bin_variables = [bin_variables]

    # Convert bin_values to list if ndarray
    if isinstance(bin_values, np.ndarray):
        bin_values = [bin_values]

    # If there is a dimension mismatch, return Error
    if len(bin_values) != len(bin_variables):
        raise ValueError(
            """Number of binning variables do not match expected number of binning
                         arrays."""
        )

    # Initialize copy to prevent overwriting original
    dataframe_out = dataframe.copy()

    # Iterate over the binning values and variables
    for variable, bins in zip(bin_variables, bin_values):
        dataframe_out.loc[:, f"{variable}_bin"] = pd.cut(dataframe_out.loc[:, variable], bins=bins)

    return dataframe_out


@patch_method_to_DataFrame(pd.DataFrame)
def bin_stats(
    dataframe: pd.DataFrame,
    bin_variable: str,
    bin_values: np.ndarray,
    contrasts: Union[str, List[str]] = [],
    variables: Union[str, List[str]] = ["length", "weight"],
    functions: Union[str, List[str]] = ["mean", "size"],
):
    """
    Quantizes dataset given user-defined intervals/bins

    Parameters
    ----------
    dataframe: pd.DataFrame
        A DataFrame object containing length and age variables required
        for analyses handling binned variables
    bin_values: np.ndarray
        An array of discrete bin values used to construct the intervals for
        the variable of interest
    bin_variable: str
        The variable that will be binned into discrete intervals
    contrasts: str or List[str]
        Additional variables to group data by, such as sex or species
    variables: str or List[str]
        Data columns to quantize
    functions: str or List[str] or List[Callable]
        Summary statistics or other functions applied to quantized variables
    """
    # Ensure that the contrasts, if there are any, are a list in case input is just a str
    con_lst = [contrasts] if isinstance(contrasts, str) else contrasts

    # Ensure variables are a list in case input is just a str
    var_lst = [variables] if isinstance(variables, str) else variables

    # Ensure functions are contained within a list
    fun_lst = [functions] if isinstance(functions, (str, Callable)) else functions

    # Rename functions as needed and if they exist
    FUNCTION_ALIASES = {
        "mean": "mean",
        "size": "n",
    }

    # Check against an allowed list
    invalid_functions = set(functions) - FUNCTION_ALIASES.keys()

    if invalid_functions:
        raise ValueError(
            f"""Invalid aggregation functions provided: {invalid_functions}.
            Only {FUNCTION_ALIASES.keys()} are allowed."""
        )

    # Construction the aggregation dictionary to apply the summary statistics toward
    aggregation_dict = {
        variable: [(f"{FUNCTION_ALIASES.get(agg, agg)}_{variable}", agg) for agg in fun_lst]
        for variable in var_lst
    }

    return (
        dataframe.bin_variable(  # input dataframe
            bin_values, bin_variable
        )  # discretize variable into bins )
        .groupby(
            [f"{bin_variable}_bin"] + con_lst, observed=False
        )  # group by these variables/contrasts
        .agg(aggregation_dict)  # apply specified functions
        .replace(np.nan, 0)  # replace NaN w/ 0's
        .droplevel(level=0, axis=1)  # drop the column indices
        .reset_index()  # reset the row indices
    )


@patch_method_to_DataFrame(pd.DataFrame)
def count_variable(
    dataframe: pd.DataFrame, contrasts: Union[str, List[str]], variable: str, fun: str
):
    """
    Quantizes dataset given user-defined intervals/bins

    Parameters
    ----------
    dataframe: pd.DataFrame
        A DataFrame object containing length and age variables required
        for analyses handling binned variables
    contrasts: str or List[str]
        Additional variables to group data by, such as sex or species
    variable: str
        Data column to bin and count
    """
    return (
        dataframe.reset_index(drop=True)  # input dataframe
        .groupby(contrasts, observed=False)
        .agg({variable: [("count", fun)]})
        .replace(np.nan, 0)
        .droplevel(level=0, axis=1)
        .reset_index()
        .sort_values(contrasts)
    )


@patch_method_to_DataFrame(pd.DataFrame)
def meld(specimen_dataframe: pd.DataFrame, length_dataframe: pd.DataFrame, contrasts: list):
    """
    Concatenates the specimen and length dataframes using a shared format

    Parameters
    ----------
    specimen_dataframe: pd.DataFrame
        A DataFrame object containing data from the specimen dataset
    length_dataframe: pd.DataFrame
        A DataFrame object containing data from the length dataset
    contrasts: list
        List of contrasts for merging the two datasets together
    """
    # Reorganize the specimen dataframe so it matches the format
    # of the length dataframe w/ length counts
    specimen_stacked = (
        specimen_dataframe.copy()
        .groupby(contrasts, observed=False)[["length"]]
        .apply(lambda x: len(x))
        .reset_index(name="length_count")
    )

    # Concatenate the data frames and return
    return pd.concat([specimen_stacked, length_dataframe], join="inner").reset_index(drop=True)


@patch_method_to_DataFrame(pd.DataFrame)
def stretch(
    dataframe,
    variable,
    variable_contrast="sex",
    index_variables=["transect_num", "latitude", "longitude", "stratum_num"],
    sep="_",
    suffix="\\w+",
):
    """
    Melts dataframe into a parseable format

    Parameters
    ----------
    dataframe: pd.DataFrame
        A DataFrame object containing pertinent biological data
    variable: str
        Data variable name
    variable_contrast: str
        The name of the column that will be used to index the data variable
    index_variables: str or List
        A list or string of additional indexing/metadata variables that will be joined to the
        data-of-interest
    sep: str
        A character indicating the separation of the variable names in the wide format, to be
        stripped from the names in the long format
    suffix: str
        A regular expression capturing the wanted suffixes
    """
    # Ensure variables are a list in case input is just a str
    idx_lst = [index_variables] if isinstance(index_variables, str) else index_variables

    # Prepare the dataframe for pivoting from wide to long
    # ---- Filter out the dataframe columns with the target index variables
    dataframe_reduced = (
        # Select the index variables
        dataframe.filter(items=idx_lst)
        # Join with the target variable
        .join(dataframe.filter(regex=variable)).drop_duplicates()
    )

    # Pivot from wide to long
    return pd.wide_to_long(
        df=dataframe_reduced,
        stubnames=variable,
        i=idx_lst,
        j=variable_contrast,
        sep=sep,
        suffix=suffix,
    ).reset_index()


@patch_method_to_DataFrame(pd.DataFrame)
def group_merge(
    dataframe: pd.DataFrame,
    dataframes_to_add: List[pd.DataFrame],
    inner_on: Optional[Union[str, List[str]]] = None,
    outer_on: Optional[Union[str, List[str]]] = None,
    how: str = "outer",
    drop_na: bool = True,
) -> pd.DataFrame:
    """
    Group merge operation for merging multiple dataframes into a parent dataframe.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Parent dataframe.
    dataframes_to_add : List[pd.DataFrame]
        List of dataframes to merge into the parent dataframe.
    inner_on : Optional[Union[str, List[str]]], optional
        Index/column name(s) used for inner merge within dataframes_to_add.
    outer_on : Optional[Union[str, List[str]]], optional
        Index/column name(s) used for outer merge between parent dataframe and dataframes_to_add.
    how : str, optional
        Type of merge to be performed, as in `pd.merge`.
    drop_na : bool, optional
        Flag to drop NaN values after merging.

    Returns
    -------
    pd.DataFrame
        Merged dataframe.

    Notes
    -----
    This function recursively merges multiple dataframes into a parent dataframe.
    """
    # Validate inputs
    if not isinstance(dataframe, pd.DataFrame):
        raise ValueError("dataframe must be a pandas DataFrame")
    if not isinstance(dataframes_to_add, list) or not all(
        isinstance(df, pd.DataFrame) for df in dataframes_to_add
    ):
        raise ValueError("dataframes_to_add must be a list of pandas DataFrames")

    # Store original data types of columns in the parent dataframe
    original_dtypes = {id(dataframe): dataframe.dtypes}
    original_dtypes.update({id(df): df.dtypes for df in dataframes_to_add})

    # Merge all dictionaries into a single dictionary with unique keys
    unique_dtypes = {}
    for dtypes_dict in original_dtypes.values():
        unique_dtypes.update(dtypes_dict.to_dict())

    # Ensure inner_on and outer_on are lists
    inner_on = inner_on if inner_on is not None else []
    outer_on = outer_on if outer_on is not None else []

    inner_on_lst = [inner_on] if isinstance(inner_on, str) else inner_on
    outer_on_lst = [outer_on] if isinstance(outer_on, str) else outer_on

    # If inner_on is None, find common columns across all dataframes_to_add
    if not inner_on:
        common_columns_inner = set.intersection(*(set(df.columns) for df in dataframes_to_add))
        inner_on_lst = list(common_columns_inner)

    # Merge dataframes within dataframes_to_add on inner_on
    if inner_on_lst:
        merged_inner_frames = reduce(
            lambda left, right: pd.merge(left, right, on=inner_on_lst, how=how), dataframes_to_add
        )
    else:
        merged_inner_frames = pd.DataFrame()

    # If outer_on is None, find common columns between dataframe and merged_inner_frames
    if not outer_on:
        common_columns_outer = set(dataframe.columns).intersection(set(merged_inner_frames.columns))
        outer_on_lst = list(common_columns_outer)

    # Merge dataframe with merged_inner_frames
    merged_frame = dataframe.merge(merged_inner_frames, on=outer_on_lst, how=how)

    # Perform merge with drop_na option
    if drop_na:
        merged_frame = merged_frame.dropna()

    # Restore original dtypes of columns in merged_frame
    for col in merged_frame.columns:
        dtype_to_restore = unique_dtypes.get(col)
        if dtype_to_restore is not None:
            if pd.api.types.is_integer_dtype(dtype_to_restore):
                # Check if column contains NaN or inf values
                if merged_frame[col].isnull().any() or not merged_frame[col].notna().all():
                    continue  # Skip conversion if NaN or inf present
                merged_frame[col] = merged_frame[col].astype(dtype_to_restore)

    return merged_frame


def group_interpolator_creator(
    grouped_data: pd.DataFrame,
    independent_var: str,
    dependent_var: str,
    contrast: Union[List[str], str],
) -> dict:

    # Check if `contrast` is a list or not
    if not isinstance(contrast, list):
        contrast = []

    # Interpolator generation helper function
    def interpolator_factory(sub_group):
        # ---- Sort the grouped values
        sub_group_sort = sub_group.sort_values(by=independent_var)
        # ---- Return the interpolation object for the specific sub-group
        return interpolate.interp1d(
            sub_group_sort[independent_var],
            sub_group_sort[dependent_var],
            kind="linear",
            bounds_error=False,
        )

    # Produce a dictionary comprising all of the produced interpolators
    interpolators = (
        grouped_data.groupby(contrast).apply(lambda group: interpolator_factory(group))
    ).to_dict()

    # Return output
    return interpolators


def compile_patterns(pattern_config: dict):
    """Compile patterns for each part in the configuration

    Parameters
    ----------
    pattern_config: dict
        Dictionary containing certain filename parts and patterns.
    """
    compiled_patterns = {}
    for part_name, part_patterns in pattern_config.items():
        compiled_patterns[part_name] = [
            re.compile(pattern, re.IGNORECASE) for pattern in [p["pattern"] for p in part_patterns]
        ]
    return compiled_patterns


def extract_parts_and_labels(region_name: str, compiled_patterns: re.Pattern, pattern_config: dict):
    """Extract corresponding labels from a region name based on compiled patterns."""

    labels = {}
    remaining_name = region_name

    for part_name, patterns in compiled_patterns.items():
        for pattern in patterns:
            match = pattern.search(remaining_name)
            if match:
                matched_value = match.group(0)
                label = next(
                    (
                        p["label"]
                        for p in pattern_config[part_name]
                        if p["pattern"] == pattern.pattern
                    ),
                    matched_value,
                )
                labels[part_name] = label if label != "None" else matched_value
                # BELOW FOR DEBUGGING
                # --------
                # extracted_parts[part_name] = matched_value
                # --------
                remaining_name = remaining_name.replace(matched_value, "", 1)
                break

    # return extracted_parts, labels
    return labels
