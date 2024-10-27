import pandas as pd

LIVE_DATA_STRUCTURE = {
    "meta": {
        "provenance": dict(),
        "date": list(),
    },
    "database": {
        "acoustics": None,
        "biology": None,
        "population": None,
    },
    "input": {
        "acoustics": {
            "nasc_df": pd.DataFrame(),
        },
        "biology": {
            "catch_df": pd.DataFrame(),
            "distributions": {
                "length_bins_df": pd.DataFrame(),
            },
            "length_df": pd.DataFrame(),
            "specimen_df": pd.DataFrame(),
        },
    },
    "results": {
        "acoustics": dict(),
        "biology": dict(),
        "stratified": dict(),
    },
}

# Required data configuration YAML structure
LIVE_CONFIG_INIT_MODEL = {
    "required_keys": ["acoustics", "biology", "geospatial"],
    "optional_keys": [],
    "keys": {
        "acoustics": {
            "required_keys": ["transmit", "TS_length_regression_parameters"],
            "optional_keys": [],
            "keys": {
                "transmit": {
                    "required_keys": ["frequency", "units"],
                    "optional_keys": [],
                    "keys": {
                        "frequency": float,
                        "units": ["Hz", "kHz"],
                    },
                },
                "TS_length_regression_parameters": {
                    "required_keys": ["*"],
                    "optional_keys": [],
                    "keys": {
                        "*": {
                            "required_keys": [
                                "number_code",
                                "TS_L_slope",
                                "TS_L_intercept",
                                "length_units",
                            ],
                            "optional_keys": ["character_code"],
                            "keys": {
                                "number_code": int,
                                "characeter_code": str,
                                "TS_L_slope": float,
                                "TS_L_intercept": float,
                                "length_units": ["mm", "cm", "m"],
                            },
                        },
                    },
                },
            },
        },
        "biology": {
            "required_keys": ["length_distribution", "catch"],
            "optional_keys": ["stations"],
            "keys": {
                "length_distribution": {
                    "required_keys": ["bins"],
                    "optional_keys": [],
                    "keys": {
                        "bins": [float, int],
                    },
                },
                "stations": {
                    "required_keys": ["separate_stations", "station_id"],
                    "optional_keys": [],
                    "keys": {
                        "separate_stations": bool,
                        "station_id": [str],
                    },
                },
                "catch": {
                    "required_keys": ["partition"],
                    "optional_keys": [],
                    "keys": {
                        "partition": str,
                    },
                },
            },
        },
        "geospatial": {
            "required_keys": ["projection", "link_biology_acoustics"],
            "optional_keys": ["inpfc", "griddify"],
            "keys": {
                "inpfc": {
                    "required_keys": ["latitude_max", "stratum_names"],
                    "optional_keys": [],
                    "keys": {
                        "latitude_max": [float],
                        "stratum_names": [int, str],
                    },
                },
                "griddify": {
                    "required_keys": ["bounds", "grid_resolution"],
                    "optional_keys": [],
                    "keys": {
                        "bounds": {
                            "required_keys": [("latitude", "longitude"), ("x", "y")],
                            "optional_keys": [],
                            "keys": {
                                "latitude": [float],
                                "longitude": [float],
                                "x": [float],
                                "y": [float],
                            },
                        },
                        "grid_resolution": {
                            "required_keys": [
                                ("latitude_distance", "longitude_distance"),
                                ("x_distance", "y_distance"),
                            ],
                            "optional_keys": [],
                            "keys": {
                                "longitude_distance": float,
                                "latitude_distance": float,
                                "x_distance": float,
                                "y_distnace": float,
                            },
                        },
                    },
                },
                "link_biology_acoustics": ["closest_haul", "global", "INPFC", "weighted_haul"],
                "projection": str,
            },
        },
    },
}

# Required data configuration YAML structure
LIVE_CONFIG_DATA_MODEL = {
    "required_keys": ["ship_id", "survey_year", "database_directory", "input_directories"],
    "optional_keys": ["species", "data_root_dir"],
    "keys": {
        "data_root_dir": str,
        "database_directory": str,
        "input_directories": {
            "required_keys": ["acoustics", "biology"],
            "optional_keys": ["coastline", "grid"],
            "keys": {
                "acoustics": {
                    "required_keys": ["database_name", "directory", "extension"],
                    "optional_keys": [],
                    "keys": {
                        "directory": str,
                        "database_name": str,
                        "extension": ["zarr"],
                    },
                },
                "biology": {
                    "required_keys": [
                        "database_name",
                        "directory",
                        "extension",
                        "file_index",
                        "file_ids",
                        "file_name_formats",
                    ],
                    "optional_keys": [],
                    "keys": {
                        "directory": str,
                        "database_name": str,
                        "extension": ["csv"],
                        "file_name_formats": {
                            "required_keys": ["*"],
                            "optional_keys": [],
                            "keys": {
                                "*": str,
                            },
                        },
                        "file_ids": {
                            "required_keys": ["*"],
                            "optional_keys": [],
                            "keys": {
                                "*": str,
                            },
                        },
                        "file_index": {
                            "required_keys": ["*"],
                            "optional_keys": [],
                            "keys": {
                                "*": [str],
                            },
                        },
                    },
                },
                "coastline": {
                    "required_keys": ["directory", "coastline_name"],
                    "optional_keys": [],
                    "keys": {
                        "directory": str,
                        "coastline_name": str,
                    },
                },
                "grid": {
                    "required_keys": ["database_name"],
                    "optional_keys": [],
                    "keys": {
                        "database_name": str,
                    },
                },
            },
        },
        "ship_id": [str, int],
        "species": {
            "required_keys": [],
            "optional_keys": ["text_code", "number_code"],
            "keys": {
                "text_code": str,
                "number_code": int,
            },
        },
        "survey_year": int,
    },
}

# TODO: Update structure with additional information (as needed)
# TODO: Documentation
LIVE_INPUT_FILE_CONFIG_MAP = {
    "acoustics": {
        "xarray_coordinates": {
            "distance": float,
            "depth": float,
        },
        "xarray_variables": {
            "NASC": float,
            "frequency_nominal": float,
            "latitude": float,
            "longitude": float,
            "ping_time": "datetime64[ns]",
        },
    },
    "biology": {
        "catch": {
            "dtypes": {
                "partition": str,
                "species_code": int,
                "overall_weight": float,
                "catch_perc": float,
            },
            "names": {
                "partition": "trawl_partition",
                "species_code": "species_id",
                "overall_weight": "haul_weight",
                "catch_perc": "catch_percentage",
            },
        },
        "trawl_info": {
            "dtypes": {
                "operation_number": int,
                "td_timestamp": str,
                "td_latitude": float,
                "td_longitude": float,
            },
            "names": {
                "operation_number": "haul_num",
                "td_timestamp": "datetime",
                "td_latitude": "latitude",
                "td_longitude": "longitude",
            },
        },
        "length": {
            "dtypes": {
                "operation_number": int,
                "partition": str,
                "sex": str,
                "rounded_length": int,
                "frequency": int,
            },
            "names": {
                "operation_number": "haul_num",
                "partition": "trawl_partition",
                "sex": "sex",
                "rounded_length": "length",
                "frequency": "length_count",
            },
        },
        "specimen": {
            "dtypes": {
                "operation_number": int,
                "partition": str,
                "length": float,
                "organism_weight": float,
                "sex": str,
            },
            "names": {
                "operation_number": "haul_num",
                "partition": "trawl_partition",
                "sex": "sex",
                "length": "length",
                "organism_weight": "weight",
            },
        },
    },
}

LIVE_FILE_FORMAT_MAP = {
    "DATE:YYYYMM": {
        "name": "date",
        "dtype": "datetime[ns]",
        "expression": r"(?P<DATE>\d{6})",
    },
    "DATE:YYYYMMDD": {
        "name": "date",
        "dtype": "datetime[ns]",
        "expression": r"(?P<DATE>\d{8})",
    },
    "HAUL": {
        "name": "haul_num",
        "dtype": int,
        "expression": r"(?P<HAUL>\d+)",
    },
    "SPECIES_CODE": {"name": "species_id", "dtype": int, "expression": r"(?P<SPECIES_CODE>\d+)"},
    "FILE_ID": {"name": "file_id", "dtype": str, "expression": r"(?P<FILE_ID>.+)"},
}

SPATIAL_CONFIG_MAP = {
    "closest_haul": {
        "proximity": {
            "choices": ["distance", "time"],
        },
    },
    "global": {},
    "griddify": {
        "bounds": {
            "longitude": {"types": [float]},
            "latitude": {"types": [float]},
            "northings": {"types": [float]},
            "eastings": {"types": [float]},
            "pairs": [("longitude", "latitude"), ("northings", "eastings")],
        },
        "grid_resolution": {
            "x_distance": {
                "types": float,
            },
            "y_distance": {
                "types": float,
            },
            "d_longitude": {
                "types": float,
            },
            "d_latitude": {
                "types": float,
            },
            "grid_size_x": {
                "types": int,
            },
            "grid_size_y": {
                "types": int,
            },
            "pairs": [
                ("x_distance", "y_distance"),
                ("d_longitude", "d_latitude"),
                ("grid_size_x", "grid_size_y"),
            ],
        },
    },
    "inpfc": {
        "stratum_names": {"types": [int, str]},
        "latitude_max": {
            "types": [float],
        },
    },
    "weighted_haul": {
        "proximity": {"choices": ["distance", "time"]},
    },
}
