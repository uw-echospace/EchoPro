import copy
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

import boto3
import numpy as np
import pandas as pd
import xarray as xr
import yaml
from botocore.exceptions import ClientError

from .live_core import (
    LIVE_CONFIG_DATA_MODEL,
    LIVE_CONFIG_INIT_MODEL,
    LIVE_FILE_FORMAT_MAP,
    LIVE_INPUT_FILE_CONFIG_MAP,
    SPATIAL_CONFIG_MAP,
)
from .live_spatial_methods import create_inpfc_strata
from .sql_methods import initialize_database, query_processed_files


# TODO: Incorporate complete YAML file validator
# TODO: Documentation
def live_configuration(
    live_init_config_path: Union[str, Path], live_file_config_path: Union[str, Path]
):

    # Validate file existence
    # ---- str-to-Path conversion, if necessary
    live_init_config_path = Path(live_init_config_path)
    live_file_config_path = Path(live_file_config_path)
    # ---- Create list of both config paths
    config_files = [live_init_config_path, live_file_config_path]
    # ---- List of file existence checks
    config_existence = [live_init_config_path.exists(), live_file_config_path.exists()]
    # ---- Error evaluation and print message (if applicable)
    if not all(config_existence):
        missing_config = [
            files for files, exists in zip(config_files, config_existence) if not exists
        ]
        raise FileNotFoundError(
            f"The following configuration files do not exist: {missing_config}."
        )

    # Read the YAML configuration/recipe file to parameterize the `LiveSurvey` class
    # ---- Initialization settings
    init_config = yaml.safe_load(Path(live_init_config_path).read_text())
    # -------- Validate
    init_config = validate_live_config(
        copy.deepcopy(init_config), LIVE_CONFIG_INIT_MODEL, live_init_config_path
    )
    # ---- Filepath/directory settings
    file_config = yaml.safe_load(Path(live_file_config_path).read_text())
    file_config = validate_live_config(
        copy.deepcopy(file_config), LIVE_CONFIG_DATA_MODEL, live_file_config_path
    )

    # Check for intersecting/duplicative configuration keys
    # ---- Compare sets of keys from each dictionary
    config_intersect = set(init_config.keys()).intersection(set(file_config.keys()))
    # ---- Raise error if needed
    if config_intersect:
        raise ValueError(
            f"The initialization and file configuration files comprise the following intersecting "
            f"keys: {' ,'.join(config_intersect)}. Key names must be unique for each configuration "
            f"file."
        )

    # Combine both into a dictionary output that can be added to the `LiveSurvey` class object
    return {**init_config, **file_config}


def read_acoustic_files(acoustic_files: List[str], xarray_kwargs: dict = {}) -> tuple:

    # Get the file-specific settings, datatypes, columns, etc.
    # ---- Get defined columns and datatypes from `LIVE_INPUT_FILE_CONFIG_MAP`
    acoustics_config_map = LIVE_INPUT_FILE_CONFIG_MAP["acoustics"]

    # Read all of the zarr files
    results_list = [
        (data_df, unit_dict) if i == 0 else (data_df, None)
        for i, (data_df, unit_dict) in enumerate(
            read_acoustic_zarr(file, acoustics_config_map, xarray_kwargs=xarray_kwargs)
            for file in acoustic_files
        )
    ]

    # Concatenate the dataframe component
    acoustic_data_df = pd.concat([df for df, _ in results_list], ignore_index=True)
    # ---- Add the `acoustic_data_units` to the dictionary and output the resulting tuple
    return acoustic_data_df, results_list[0][1] if results_list else None


def filter_filenames(
    directory_path: Path, filename_id: str, files: List[Path], file_extension: str
):

    # Drop the `{FIELD_ID}` tag identifier
    file_id_format = re.sub(r"\{FILE_ID:([^}]+)\}", r"\1", filename_id)
    # ---- Replace all other tags with `*` placeholders
    file_id_format = re.sub(r"\{[^{}]+\}", "*", file_id_format)
    # ---- Compile the pattern
    escaped_file_id_format = re.escape(file_id_format)
    pattern = re.compile(escaped_file_id_format.replace(r"\*", ".*"))
    # pattern = re.compile(rf'{file_id_format.replace(".", r"\.").replace("*", ".*")}')
    # ---- Create Path object with the generalized format: S3
    s3_files = [
        filename for filename in files if filename.startswith("s3://") and pattern.search(filename)
    ]
    # ---- Local search
    local_files = Path(directory_path).glob(f"{file_id_format}.{file_extension}")
    # ---- Assign to subfile path object
    if s3_files:
        subfile_path_obj = s3_files
    else:
        subfile_path_obj = local_files
    # ---- List all files that match this pattern
    subfile_str = [str(file) for file in list(subfile_path_obj)]

    # Convert list of proposed files from Path to String
    file_str = [str(file) for file in list(files)]

    # Find intersection with the proposed filenames and return the output
    return list(set(subfile_str).intersection(set(file_str)))


def read_biology_files(
    biology_files: List[str], file_configuration: dict, pandas_kwargs: dict = {}
):

    # Get the biology data file settings
    file_settings = file_configuration["input_directories"]["biology"]

    # Get the file-specific settings, datatypes, columns, etc.
    # ---- Get defined columns and datatypes from `LIVE_INPUT_FILE_CONFIG_MAP`
    biology_config_map = LIVE_INPUT_FILE_CONFIG_MAP["biology"]
    # ---- Extract the expected file name ID's
    biology_file_ids = file_settings["file_name_formats"]
    # ---- Extract all of the file ids
    biology_config_ids = list(biology_file_ids.keys())
    # ---- Initialize the dictionary that will define this key in the `input` attribute
    biology_output = {f"{key}_df": pd.DataFrame() for key in biology_config_ids}
    # # ---- Create filepath object
    if "data_root_dir" in file_configuration:
        # directory_path = Path(file_configuration["data_root_dir"]) / file_settings["directory"]
        directory_path = "/".join([file_configuration["data_root_dir"], file_settings["directory"]])
    else:
        directory_path = file_settings["directory"]

    # Add SQL file to dict
    # file_configuration["database"]["biology"] = (
    #     Path(file_configuration["data_root_dir"]) / "database" / file_settings["database_name"]
    # )
    file_configuration["database"]["biology"] = (
        # Path(file_configuration["database_directory"]) / file_settings["database_name"]
        "/".join([file_configuration["database_directory"], file_settings["database_name"]])
    )

    # Iterate through the different biology datasets and read them in
    for dataset in list(biology_file_ids.keys()):
        # ---- Get dataset-specific file lists
        dataset_files = filter_filenames(
            directory_path, biology_file_ids[dataset], biology_files, file_settings["extension"]
        )
        # ---- If there are dataset files available
        if dataset_files:
            # ---- Read in validated biology data
            dataframe_list = [
                read_biology_csv(
                    file,
                    file_settings["file_name_formats"][dataset],
                    biology_config_map[dataset],
                    pandas_kwargs,
                )
                for file in dataset_files
            ]
            # ---- Concatenate the dataset
            dataframe_combined = pd.concat(dataframe_list, ignore_index=True)
            # ---- Lower-case sex
            if "sex" in dataframe_combined.columns:
                dataframe_combined["sex"] = dataframe_combined["sex"].str.lower()
            # ---- Lower-case trawl partition type
            if "trawl_partition" in dataframe_combined.columns:
                dataframe_combined["trawl_partition"] = dataframe_combined[
                    "trawl_partition"
                ].str.lower()
            # ---- Reformat datetime column
            if "datetime" in dataframe_combined.columns:
                dataframe_combined["datetime"] = convert_datetime(dataframe_combined["datetime"])
            # ---- Add to the data dictionary
            biology_output[f"{dataset}_df"] = dataframe_combined

    # Return the output
    return biology_output


def read_acoustic_zarr(file: Path, config_map: dict, xarray_kwargs: dict = {}) -> tuple:

    # Format the file reading configuration
    # ---- Concatenate into a full configuration map
    full_config_map = {**config_map["xarray_coordinates"], **config_map["xarray_variables"]}

    # Determine the file loading method for the `acoustic_files`
    zarr_data_ds = xr.open_dataset(file, engine="zarr", chunks="auto", **xarray_kwargs)

    # Pre-process the Dataset, convert it to a DataFrame, and validate the structure
    # ---- Convert to a DataFrame
    zarr_data_df = zarr_data_ds.to_dataframe().reset_index()
    # ---- Check for any missing columns
    missing_columns = [key for key in full_config_map.keys() if key not in zarr_data_df.columns]
    # ---- Raise Error, if needed
    if missing_columns:
        raise ValueError(
            f"The following columns are missing from at least one file: in "
            f"{', '.join(missing_columns)}!"
        )
    # ---- Select defined columns
    zarr_data_df_filtered = zarr_data_df[full_config_map.keys()].astype(full_config_map)

    # Add the filename as a column
    zarr_data_df_filtered["source"] = Path(file).name

    # Gather some of the units
    data_units = {
        "longitude": zarr_data_ds.longitude.units,
        "latitude": zarr_data_ds.latitude.units,
        "frequency": zarr_data_ds.frequency_nominal.units,
    }

    # Return a Tuple
    return zarr_data_df_filtered, data_units


def construct_directorypath(file_configuration: dict, file_settings: dict):
    """Construct the root directory path."""

    # Get the general root_directory, if present
    if "data_root_dir" in file_configuration:
        root_directory = file_configuration["data_root_dir"]
    else:
        root_directory = ""

    # Get the local directory (or this may be the root directory depending on the config)
    data_directory = file_settings["directory"]

    # Return the directory path
    if root_directory != "":
        return "/".join([root_directory, data_directory])
    else:
        return data_directory


def is_s3_path(path):
    """Check if a path is an S3 path."""
    return path.startswith("s3://")


# TODO: Documentation
def validate_data_directory(
    file_configuration: dict, dataset: str, input_filenames: Optional[list] = None
) -> List[Path]:

    # Get the dataset file settings
    file_settings = file_configuration["input_directories"][dataset]

    # Get the data file settings and directorypath
    directory_path = construct_directorypath(file_configuration, file_settings)

    # Validate `input_filenames` input
    if input_filenames is not None and not isinstance(input_filenames, list):
        raise TypeError("Data loading argument `input_filenames` must be a list.")

    # Format data filenames
    if input_filenames is not None:
        data_files = ["/".join([directory_path, filename]) for filename in input_filenames]

    # Validate directories and format filepath names
    # ---- S3 bucket
    if is_s3_path(directory_path):
        # ---- Validate
        validate_s3_path(directory_path, file_configuration["storage_options"])
        # ---- Format data files
        if input_filenames is None:
            data_files = []
    # ---- Local
    else:
        # ---- Validate
        validate_local_path(directory_path, file_settings)
        # ---- Format data files
        if input_filenames is None:
            data_files = list(Path(directory_path).glob(f"*{'.'+file_settings['extension']}"))

    # Clean the filenames
    data_files = [
        (
            re.sub(r"//", r"\\", str(filename)).replace("/", "\\")
            if not str(filename).startswith("s3://")
            else str(filename)
        )
        for filename in data_files
    ]

    # Database root directory
    database_root_directory = file_configuration["database_directory"]

    # Initialize the database file
    initialize_database(database_root_directory, file_settings)

    # Drop incomplete datasets
    if dataset == "biology":
        data_files = validate_complete_biology_dataset(
            data_files, directory_path, file_configuration
        )

    # Query the SQL database to process only new files (or create the db file in the first place)
    valid_files, file_configuration["database"][dataset] = query_processed_files(
        database_root_directory, file_settings, data_files
    )

    # Return the valid filenames/paths
    return valid_files


def validate_s3_path(s3_path: str, cloud_credentials: dict):
    """Check if (parts of) S3 path exists."""

    # Redundant validation that S3 object validation is appropriate
    if not is_s3_path(s3_path):
        raise ValueError("The path is not an S3 path.")

    # Validate credentials
    if not all(
        [True if param in cloud_credentials.keys() else False for param in ["key", "secret"]]
    ):
        # ---- Find missing credentials
        missing_creds = set(["key", "secret"]) - set(cloud_credentials)
        # ---- Format into string
        missing_creds_str = ", ".join(["'{}'".format(x.replace("'", "''")) for x in missing_creds])
        # ---- Raise Error
        raise PermissionError(f"Required S3 credentials missing: {missing_creds_str}.")

    # Remove the s3:// prefix
    s3_path_reduced = s3_path[len("s3://") :]

    # Split into bucket and key
    parts = s3_path_reduced.split("/", 1)
    if len(parts) < 2:
        raise ValueError(f"Invalid S3 path format for '{s3_path}'.")

    # Get bucket name and directory keys
    bucket_name, directory = parts

    # Initialize the S3 client
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=cloud_credentials["key"],
        aws_secret_access_key=cloud_credentials["secret"],
    )

    # Check if the bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        raise FileNotFoundError(
            f"S3 bucket '{bucket_name}' does not exist or you do not have access."
        )

    # Check if the S3 directory exists
    try:
        # ---- Ping a response from the bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=directory, MaxKeys=1)
        # ---- Check for `Contents`
        if "Contents" not in response:
            raise FileNotFoundError(f"S3 path '{s3_path}' does not exist.")
    except ClientError as e:
        # --- Raise Error and propagate it upwards
        raise e


def validate_local_path(directory_path: str, file_settings: dict):

    # Validate filepath
    # ---- Error evaluation (if applicable)
    if not Path(directory_path).exists():
        raise FileNotFoundError(f"The data directory [{directory_path}] does not exist.")

    # Validate that files even exist
    # ---- List available files of target extension
    data_files = list(Path(directory_path).glob(f"*{'.'+file_settings['extension']}"))
    # ---- Error evaluation (if applicable)
    if not data_files:
        raise FileNotFoundError(
            f"No `*.{file_settings['extension']}` files found in [{directory_path}]!"
        )


def validate_complete_biology_dataset(
    data_files: List[str], directory_path: str, file_configuration: dict
):

    # Get the biology data file settings
    file_settings = file_configuration["input_directories"]["biology"]

    # Get the file-specific settings, datatypes, columns, etc.
    # ---- Extract the expected file name ID's
    biology_file_ids = file_settings["file_name_formats"]

    # Define helper function for extract haul number from filename strings
    def get_file_haul_number(filename, format_string):
        # Step 1: Extract the filename from the full path
        filename_only = os.path.basename(filename)

        # Remove the file extension from the filename
        filename_no_ext = os.path.splitext(filename_only)[0]

        # Split the format string and filename into parts
        format_parts = re.findall(r"\{[^}]+\}|[^_]+", format_string)
        filename_parts = filename_no_ext.split("_")

        # Find the index of {HAUL} in format_parts
        haul_index = format_parts.index("{HAUL}")

        # Extract and return the haul number from filename_parts
        if haul_index < len(filename_parts):
            return filename_parts[haul_index]
        return None

    # Organize dataset by their respective dataset-type
    dataset_dict = {
        key: filter_filenames(directory_path, ds, data_files, file_settings["extension"])
        for key, ds in biology_file_ids.items()
    }

    # Extract the haul numbers
    extracted_hauls = {
        key: set(
            get_file_haul_number(filename, biology_file_ids.get(key, "")) for filename in filenames
        )
        for key, filenames in dataset_dict.items()
    }

    # Find haul numbers that appear in all keys
    common_hauls = set.intersection(*extracted_hauls.values())

    # Filter filenames to keep only those with haul numbers in the common set
    filtered_filenames = [
        filename
        for key, filenames in dataset_dict.items()
        for filename in filenames
        if get_file_haul_number(filename, biology_file_ids.get(key, "")) in common_hauls
    ]

    # Get bad files for DEBUG
    non_filtered_filenames = [
        filename
        for key, filenames in dataset_dict.items()
        for filename in filenames
        if get_file_haul_number(filename, biology_file_ids.get(key, "")) not in common_hauls
    ]
    # ---- Create list
    non_filtered_filenames_lst = "\n".join(non_filtered_filenames)
    print(
        f"The following files are parts of incomplete filesets: \n" f"{non_filtered_filenames_lst}"
    )

    # Return the curated filename list
    return filtered_filenames


def compile_filename_format(file_name_format: str):

    # Create a copy of `file_name_format`
    regex_pattern = file_name_format

    # Iterate through the keys from `LIVE_FILE_FORMAT_MAP` to format a regex pattern
    for key, value in LIVE_FILE_FORMAT_MAP.items():
        regex_pattern = regex_pattern.replace(f"{{{key}}}", value["expression"])
    # ---- Replace the `FILE_ID` tag
    regex_pattern = re.sub(r"\{FILE_ID:(.+?)\}", r"(?P<FILE_ID>\1)", regex_pattern)

    # Compile the regex pattern and return the output
    return re.compile(regex_pattern)


def read_biology_csv(file: Path, pattern: re.Pattern, config_map: dict, pandas_kwargs: dict = {}):

    # Read in the `*.csv` file
    df = pd.read_csv(file, usecols=list(config_map["dtypes"].keys()), storage_options=pandas_kwargs)

    # Validate the dataframe
    # ---- Check for any missing columns
    missing_columns = [key for key in config_map["dtypes"].keys() if key not in df.columns]
    # ---- Raise Error, if needed
    if missing_columns:
        raise ValueError(
            f"The following columns are missing from [{file}]: {', '.join(missing_columns)}!"
        )
    # ---- Ensure the correct datatypes
    df_validated = df.astype(config_map["dtypes"])
    # ---- Replace column names and drop
    df_validated = df_validated.rename(columns=config_map["names"])

    # Get the substring components that can be added to the DataFrame
    filename_substrings = re.findall(r"\{([^:}]+)(?::[^}]+)?}", pattern)
    # ---- Create sub-list of columns that can be added to the DataFrame
    valid_tags = list(set(["HAUL", "SPECIES_CODE"]).intersection(set(filename_substrings)))

    # Compile the filename regular expression
    compiled_regex = compile_filename_format(pattern)
    # ---- Create the `Match` object that will be used to parse the string
    match_obj = compiled_regex.search(file)

    # Iterate through the filename-derived tags and add them to the DataFrame
    for i in valid_tags:
        matched_key = LIVE_FILE_FORMAT_MAP[i]
        df_validated[matched_key["name"]] = matched_key["dtype"](match_obj.group(i))

    # Return the resulting DataFrame
    return df_validated


def infer_datetime_format(timestamp_str: Union[int, str]):
    patterns = {
        r"^\d{14}$": "%Y%m%d%H%M%S",  # YYYYMMDDHHMMSS
        r"^\d{8}$": "%Y%m%d",  # YYYYMMDD
        r"^\d{6}$": "%H%M%S",  # HHMMSS
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$": "%Y-%m-%d %H:%M:%S",  # YYYY-MM-DD HH:MM:SS
        r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}$": "%Y/%m/%d %H:%M:%S",  # YYYY/MM/DD HH:MM:SS
        r"^\d{4}-\d{2}-\d{2}$": "%Y-%m-%d",  # YYYY-MM-DD
        r"^\d{4}/\d{2}/\d{2}$": "%Y/%m/%d",  # YYYY/MM/DD
    }

    for pattern, date_format in patterns.items():
        if re.match(pattern, timestamp_str):
            return date_format

    raise ValueError("Unknown timestamp format")


def convert_datetime(timestamp: Union[int, str, pd.Series]):

    if isinstance(timestamp, pd.Series):
        test_timestamp = str(timestamp[0])
    else:
        test_timestamp = str(timestamp)

    # Approximate the datetime format
    datetime_format = infer_datetime_format(str(test_timestamp))

    #
    if isinstance(timestamp, pd.Series):
        return timestamp.apply(lambda x: datetime.strptime(x, datetime_format))
    else:
        return datetime.strptime(timestamp, datetime_format)


def validate_hauls_config(spatial_config: dict, link_method: str):

    # Get the link method configuration map
    link_method_settings = SPATIAL_CONFIG_MAP[link_method]

    # Extract the defined settings
    input_method_settings = spatial_config[link_method]

    # Check for `proximity`
    if "proximity" not in input_method_settings.keys():
        raise KeyError(
            "The following parameters are missing from the biology-acoustic linking method: "
            "'proximity'!"
        )

    # Evaluate valid options for `proximity`
    if input_method_settings["proximity"] not in link_method_settings["proximity"]["choices"]:
        raise KeyError(
            f"Value biology-acoustic linking method parameter `proximity` must be one of the : "
            f"following: {link_method_settings['proximity']['choices']}."
        )


def validate_griddify_config(spatial_config: dict, link_method: str):

    # Get the link method configuration map
    link_method_settings = SPATIAL_CONFIG_MAP[link_method]

    # Extract the defined settings
    input_method_settings = spatial_config[link_method]

    # Check for the required keys
    key_diff = set(input_method_settings.keys()).difference(set(link_method_settings.keys()))
    # ---- Raise Error
    if key_diff:
        raise KeyError(
            f"The following parameters are missing from the biology-acoustic linking method: "
            f"{list(key_diff)}!"
        )

    # Iterate through the keys to evaluate inputs
    for key in list(input_method_settings.keys()):
        # ---- Subset the input method config
        input = input_method_settings[key]
        # ---- Get the original config of the dtypes
        model = link_method_settings[key]
        # ---- Compare entries
        parameter_diff = set(input.keys()).difference(set(model.keys()))
        # ---- Raise Error
        if parameter_diff:
            raise KeyError(
                f"Unexpected parameter(s) ('{parameter_diff}') detected in '{link_method}' "
                f"configuration."
            )
        # ---- Check if the appropriate coordinate pairs are present
        coordinate_pairs = [set(param).intersection(set(input.keys())) for param in model["pairs"]]
        # ---- Count the number of paired coordinates
        pair_counts = [len(param) for param in coordinate_pairs]
        # ---- If there are multiple pairs
        if (np.array(pair_counts) == 2).sum() != 1:
            raise ValueError(
                f"A single coordinate-pair is allowed (and required) within the '{key}' parameter "
                f"for the link method '{link_method}' defined via the following options: "
                f"{model['pairs']}."
            )
        # ---- Check the datatypes
        for parameter in input.keys():
            # ---- Get the datatypes
            config_dtypes = model[parameter]["types"]
            # ---- Get input parameter
            input_parameter = input[parameter]
            # ---- If List
            if isinstance(config_dtypes, list):
                if not isinstance(input_parameter, list):
                    raise TypeError(
                        f"Biology-acoustic linking method argument '{parameter}' within '{key}' "
                        f"for method '{link_method}' must be contained within a list."
                    )
            else:
                input_parameter = [input_parameter]
                config_dtypes = [config_dtypes]
            # ---- Check correct datatypes
            if not np.all([type(value) in config_dtypes for value in input_parameter]):
                raise TypeError(
                    f"Biology-acoustic linking method argument '{parameter}' within '{key}' "
                    f"for method '{link_method}' must be one of the following types within a list: "
                    f"{config_dtypes}."
                )


def validate_inpfc_config(spatial_config: dict, link_method: str):

    # Get the link method configuration map
    link_method_settings = SPATIAL_CONFIG_MAP[link_method]

    # Extract the defined settings
    input_method_settings = spatial_config[link_method]

    # Check for the required keys
    key_diff = set(input_method_settings.keys()).difference(set(link_method_settings.keys()))
    # ---- Raise Error
    if key_diff:
        raise KeyError(
            f"The following parameters are missing from the biology-acoustic linking method: "
            f"{list(key_diff)}!"
        )

    # Iterate through the keys to evaluate inputs
    for key in list(input_method_settings.keys()):
        # ---- Subset the input method config
        input = input_method_settings[key]
        # ---- Get the original config of the dtypes
        model = link_method_settings[key]["types"]
        # ---- Evaluate if a list
        if not isinstance(input, list):
            raise TypeError(
                f"Biology-acoustic linking method argument '{key}' for method '{link_method}' must "
                f"be contained within a list."
            )
        # ---- Evaluate if it is a type within the list
        if not type(input[0]) in model:
            raise TypeError(
                f"Biology-acoustic linking method argument '{key}' for method '{link_method}' must "
                f"be one of the following types within a list: {model}."
            )


def configure_spatial_settings(file_configuration: dict):

    # Extract spatial strata *only* if spatial information from the configuration settings
    # ---- Get (geo)spatial config
    spatial_config = file_configuration["geospatial"]
    # ---- Remove case sensitivity
    spatial_config = {key.lower(): value for key, value in spatial_config.items()}
    # ---- Extract the biology-acoustics linking method options
    acoustics_biology_link = spatial_config["link_biology_acoustics"]

    # Validate the configuration
    validate_spatial_config(spatial_config)

    # Create spatial dictionary that will be added as an `input`
    spatial_dict = {"link_method": acoustics_biology_link}

    # Assign the spatial link constraints to the acoustic and biological data
    if acoustics_biology_link == "INPFC":
        # ---- Update spatial dictionary
        spatial_dict.update({"strata": create_inpfc_strata(spatial_config)})
        # ---- Update the stratum classification in the primary file configuration
        file_configuration.update({"spatial_column": ["stratum"]})
    else:
        # ---- Empty `spatial_column` key
        file_configuration.update({"spatial_column": []})

    # Add grid
    file_configuration.update(
        {"gridding_column": file_configuration["spatial_column"] + ["x", "y"]}
    )

    # Return the dictionary as an output
    return spatial_dict


def validate_spatial_config(spatial_config: dict):

    # Check the link method
    # ---- Extract string-formatted method name
    link_method = spatial_config["link_biology_acoustics"].lower()
    # ---- Validate
    if link_method not in SPATIAL_CONFIG_MAP.keys():
        raise ValueError(
            f"Unexpected biology-acoustic linking parameter ([{link_method}]). Valid options "
            f"include: 'global', 'closest_haul', 'weighted_haul', 'griddify', and 'INPFC'."
        )

    # Verify that associated parameters are present in the configuration settings
    # ---- Get keys as a list
    config_keys = list(spatial_config.keys())
    # ---- Check for specific methods
    if link_method not in config_keys and link_method != "global":
        raise ValueError(
            f"No parameters provided for the biology-acoustic linking ([{link_method}])."
        )

    # Check key settings
    if link_method == "griddify":
        validate_griddify_config(spatial_config, link_method)
    elif link_method == "inpfc":
        validate_inpfc_config(spatial_config, link_method)
    elif link_method != "global":
        validate_hauls_config(spatial_config, link_method)


def validate_live_config(config: dict, reference_model: dict, filename: Union[str, Path]):
    """Validate configuration inputs"""

    # Convert to string if Path
    if isinstance(filename, Path):
        filename = str(filename)

    # Recursive function for validating entire nested dictionary
    def validate_keys(config, model, path=""):

        # Get the required/optional/actual keys
        # ---- Keys that are required by the software
        required_keys = model.get("required_keys", [])
        # ---- Keys that are optionally incorporated into the software
        optional_keys = model.get("optional_keys", [])
        # ---- Navigate the nested branches
        keys = model.get("keys", {})

        # General helper functions
        # ----
        def get_keys_from_tuples(tuples):
            """Parse key names from tuples"""
            return {key for group in tuples if isinstance(group, tuple) for key in group}

        # ----
        def find_missing_keys(required_keys, keys_to_check):
            """Find any missing keys"""
            all_required_keys = get_keys_from_tuples(required_keys)
            valid_keys_in_tuples = set()
            for group in required_keys:
                if isinstance(group, tuple):
                    if any(key in keys_to_check for key in group):
                        valid_keys_in_tuples.update(group)
            missing_keys = [key for key in valid_keys_in_tuples if key not in keys_to_check]
            unexpected_keys = [key for key in keys_to_check if key not in all_required_keys]
            return missing_keys, unexpected_keys

        # ----
        def check_for_missing_keys(required_keys, config_keys, path):
            """Check whether any required keys are missing"""
            missing_required = []
            for key in required_keys:
                if isinstance(key, tuple):
                    missing_keys, unexpected_keys_for_keys = find_missing_keys(
                        required_keys, config_keys
                    )
                    if missing_keys:
                        raise ValueError(
                            f"Missing required configuration key(s): "
                            f"{', '.join(missing_keys)} at {path} in configuration file "
                            f"'{filename}'."
                        )
                    return unexpected_keys_for_keys
                elif key not in config_keys and key != "*":
                    missing_required.append(key)
            if missing_required:
                raise ValueError(
                    f"Missing required configuration key(s): {', '.join(missing_required)} at "
                    f"{path} in configuration file '{filename}'."
                )
            return []

        # ----
        def check_for_unexpected_keys(config_keys, required_keys):
            """Check for unexpected keys"""
            unexpected_keys = []
            for key in config_keys:
                if (
                    key not in required_keys
                    and key not in optional_keys
                    and "*" not in required_keys
                ):
                    if not any(key in group for group in required_keys if isinstance(group, tuple)):
                        unexpected_keys.append(key)
            return unexpected_keys

        # Top-level validation
        if path == "":
            missing_primary_keys = [
                key for key in required_keys if key != "*" and key not in config
            ]
            if missing_primary_keys:
                raise ValueError(
                    f"Missing primary configuration key(s): {', '.join(missing_primary_keys)} in "
                    f"configuration file '{filename}'."
                )
            unexpected_primary_keys = [
                key
                for key in config
                if key not in required_keys
                and key not in optional_keys
                and "*" not in required_keys
            ]
            # ---- Raise error
            if unexpected_primary_keys:
                raise ValueError(
                    f"Unexpected primary key(s) found in configuration file '{filename}': "
                    f"{', '.join(unexpected_primary_keys)}"
                )
        # Nested validation
        else:
            config_keys = config.keys()
            unexpected_keys = check_for_missing_keys(required_keys, config_keys, path)
            unexpected_keys.extend(check_for_unexpected_keys(config_keys, required_keys))
            # ---- Raise error
            if unexpected_keys:
                raise ValueError(
                    f"Unexpected key(s) found: {', '.join(unexpected_keys)} at {path} in "
                    f"configuration file '{filename}'."
                )

        # Recursively validate nested dictionaries and lists
        for key, sub_model in keys.items():
            if key == "*" and isinstance(sub_model, dict):
                for sub_key in config:
                    validate_keys(
                        config[sub_key], sub_model, path=f"{path}.{sub_key}" if path else sub_key
                    )
            elif key == "*" and isinstance(sub_model, list):
                for sub_key in config:
                    validate_list(config[sub_key], sub_model, key, path)
            elif key == "*":
                for sub_key in config:
                    validate_type(config[sub_key], sub_model, key, path)
            elif key in config:
                if isinstance(sub_model, dict):
                    validate_keys(config[key], sub_model, path=f"{path}.{key}" if path else key)
                elif isinstance(sub_model, list):
                    validate_list(config[key], sub_model, key, path)
                else:
                    validate_type(config[key], sub_model, key, path)

    # Additional helper functions
    # ----
    def validate_list(config_value, allowed_types, key, path):
        """Validate configuration with model that is formatted as a list"""
        if all(isinstance(item, (str, int, float)) for item in allowed_types):
            if config_value not in allowed_types:
                raise ValueError(
                    f"Invalid value for key '{key}' at {path} in {filename}. Expected one of: "
                    f"{allowed_types}"
                )
        elif not isinstance(config_value, list):
            if type(config_value) not in allowed_types:
                raise ValueError(
                    f"Invalid value for key '{key}' at {path} in {filename}. Expected one of: "
                    f"{allowed_types}"
                )
        else:
            if isinstance(config_value, list):
                for item in config_value:
                    if not any(isinstance(item, t) for t in allowed_types):
                        raise ValueError(
                            f"Invalid type for items in list '{key}' at {path} in {filename}. "
                            f"Expected one of: {allowed_types}"
                        )
            else:
                raise ValueError(
                    f"Invalid type for key '{key}' at {path} in {filename}. Expected a list of: "
                    f"{allowed_types}"
                )

    # ----
    def validate_type(config_value, expected_type, key, path):
        """Validate configuration with model that is at the furthest point along a branch"""
        if not isinstance(config_value, expected_type):
            raise ValueError(
                f"Invalid type for key '{key}' at {path} in {filename}. Expected type: "
                f"{expected_type}"
            )

    # Validate all branches within the configuration dictionary
    validate_keys(config, reference_model)

    # Return
    return config
