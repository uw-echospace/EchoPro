# import contextlib
# import copy
# import glob
# import os
# import re
# from datetime import datetime
# from pathlib import Path
# from typing import Optional, Tuple, Union

# import geopandas as gpd
# import matplotlib.cm as cm
# import matplotlib.colors as colors
# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# import shapely.geometry
# import xarray as xr
# import yaml
# from geopy.distance import distance
# from matplotlib.colors import ListedColormap
# from shapely import wkt
# from shapely.geometry import box
# from sqlalchemy import Engine, create_engine, inspect, text

# from echopop.acoustics import to_dB, to_linear, ts_length_regression
# from echopop.live import live_data_loading as eldl, live_data_processing as eldp
# from echopop.live.live_acoustics import configure_transmit_frequency, integrate_nasc
# from echopop.live.live_biology import preprocess_biology_data
# from echopop.live.live_core import (
#     LIVE_DATA_STRUCTURE,
#     LIVE_FILE_FORMAT_MAP,
#     LIVE_INPUT_FILE_CONFIG_MAP,
#     SPATIAL_CONFIG_MAP,
# )
# from echopop.live.live_data_loading import validate_data_directory
# from echopop.live.live_data_processing import get_unique_identifiers, query_dataset
# from echopop.live.live_survey import LiveSurvey
# from echopop.live.sql_methods import (
#     SQL,
#     SQL_COMMANDS,
#     format_sql_columns,
#     initialize_database,
#     query_processed_files,
#     sql_data_exchange,
#     sql_group_update,
#     sql_update_strata_summary,
# )
# from echopop.spatial.projection import utm_string_generator
# from echopop.survey import Survey

# self = realtime_survey
# spatial_config = self.config["geospatial"]
# dataset = self.input["acoustics"]["nasc_df"]


# survey_2019 = Survey("C:/Users/Brandyn/Documents/GitHub/echopop/config_files/initialization
# _config.yml", "C:/Users/Brandyn/Documents/GitHub/echopop/config_files/survey_year_2019_config
# .yml")
# survey_2019.transect_analysis()
# survey_2019.analysis["transect"]["biology"]["weight"]["weight_stratum_df"]
# analysis_dict = survey_2019.analysis["transect"]
# SQL(acoustic_db, "select", table_name="sigma_bs_mean_df")
# proportions_dict=analysis_dict["biology"]["proportions"]["number"]
# length_weight_dict = analysis_dict["biology"]["weight"]
# stratum_proportions_sexed["proportion_aged"] + stratum_proportions_sexed["proportion_unaged"]

# updated_survey_data = nasc_biology.copy()
# gridding_column = file_configuration["gridding_column"]

# unique_keys = get_unique_identifiers(updated_survey_data, gridding_column)


# file_configuration = self.config
# grid_settings["grid_resolution"]["x"] = 50
# grid_settings["grid_resolution"]["y"] = 50
# lat_step = distance(nautical=grid_settings["grid_resolution"]["x"]).meters
# lon_step = distance(nautical=grid_settings["grid_resolution"]["y"]).meters
# self = realtime_survey
# file_configuration = self.config

# def initialize_grid():

#     # Get root directory, if defined
#     if "data_root_dir" in file_configuration:
#         root_dir = Path(file_configuration["data_root_dir"])
#     else:
#         root_dir = Path()

#     # Get `grid` settings
#     grid_database = file_configuration["input_directories"]["grid"]["database_name"]

#     # Create full filepath
#     db_filepath = root_dir / "database" / grid_database

#     # Create if file doesn't already exist
#     if not db_filepath.exists():

#         # Get projection
#         projection = file_configuration["geospatial"]["projection"]

#         # Get grid settings
#         grid_settings = file_configuration["geospatial"]["griddify"]

#         # Get the resolution
#         resolution = grid_settings["grid_resolution"]
#         # ---- Convert from nmi to m
#         resolution_m = {key: distance(nautical=dist).meters for key, dist in resolution.items()}

#         # Get boundary coordinates
#         boundary = grid_settings["bounds"]
#         # ---- x
#         x = boundary["longitude"]
#         # ---- y
#         y = boundary["latitude"]
#         # ---- Create DataFrame
#         boundary_df = pd.DataFrame({
#             "x": np.array([np.min(x), np.max(x), np.max(x), np.min(x), np.min(x)]),
#             "y": np.array([np.min(y), np.min(y), np.max(y), np.max(y), np.min(y)])
#         })

#         # Create GeoDataFrame
#         boundary_gdf = gpd.GeoDataFrame(
#             data = boundary_df,
#             geometry=gpd.points_from_xy(boundary_df["x"], boundary_df["y"]),
#             crs = projection
#         )

#         # Convert to UTM (decimal degrees to m)
#         # ---- Create UTM code
#         utm_code = utm_string_generator((boundary_df.x.min() + boundary_df.x.max()) / 2,
#                                         (boundary_df.y.min() + boundary_df.y.max()) / 2)
#         # ---- Create number code
#         utm_num = int(utm_code)
#         # ---- Create string code
#         utm_str = f"epsg:{utm_num}"
#         # ---- UTM conversion
#         boundary_gdf_utm = boundary_gdf.to_crs(utm_num)

#         # Get step sizes for each grid cell
#         # ---- x
#         x_step = resolution_m["x_distance"]
#         # ---- y
#         y_step = resolution_m["y_distance"]

#         # Prepare grid cell generation
#         # ---- Get new boundaries
#         xmin, ymin, xmax, ymax = boundary_gdf_utm.total_bounds
#         # ---- Initialize empty list
#         grid_cells = []
#         # ---- Initialize coordinate counter
#         y_ct = 0
#         x_coord = []; y_coord = []
#         # ---- Iterate through to generate cells
#         for y0 in np.arange(ymin, ymax, y_step):
#             y_ct += 1
#             x_ct = 0
#             for x0 in np.arange(xmin, xmax, x_step):
#                 x_ct += 1
#                 # ---- Step forward
#                 x_coord.append(x_ct)
#                 y_coord.append(y_ct)
#                 x1 = x0 - x_step
#                 y1 = y0 + y_step
#                 # ---- Append to list
#                 grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))

#         # Convert to a GeoDataFrame
#         cells_gdf = gpd.GeoDataFrame(grid_cells, columns=["geometry"], crs=utm_code)
#         # ---- Add coordinates
#         cells_gdf.loc[:, "x"] = np.array(x_coord)
#         cells_gdf.loc[:, "y"] = np.array(y_coord)

#         # Get coastline shapefile directory, if defined
#         if "coastline" in file_configuration["input_directories"]:

#             # Get coastline settings
#             coast_settings = file_configuration["input_directories"]["coastline"]
#             # ---- Create filepath
#             shp_filepath = (
#                 root_dir / coast_settings["directory"]
#                 / coast_settings["coastline_name"] / f"{coast_settings["coastline_name"]}.shp"
#             )
#             # ---- Validate existence
#             if not shp_filepath.exists():
#                 raise FileNotFoundError(
#                     f"{shp_filepath} does not exist!"
#                 )

#             # Get original lat/lon geometry boundaries
#             xmin0, ymin0, xmax0, ymax0 = boundary_gdf.total_bounds

#             # Read in file
#             full_coast = gpd.read_file(shp_filepath)
#             # ---- Convert to UTM
#             full_coast_utm = full_coast.to_crs(utm_code)
#             # ---- Remove empty
#             full_coast_utm = full_coast_utm[~full_coast_utm.is_empty]

#             # Create bounding box with a buffer
#             boundary_box = box(xmin0 - 5, ymin0 - 5, xmax0 + 5, ymax0 + 5)
#             # ---- Create an unbuffered copy
#             boundary_box_unbuffered = box(xmin0, ymin0, xmax0, ymax0)
#             # ---- Convert to a GeoDataFrame
#             boundary_box_unbuffered_gdf = (
#                 gpd.GeoDataFrame(geometry=[boundary_box_unbuffered], crs=projection)
#             )
#             # ---- Clip the coastline for saving
#             clipped_coast_original = (
#                 gpd.clip(full_coast, box(xmin0 + 1, ymin0 + 1, xmax0 + 1, ymax0 + 1))
#             )

#             # Clip the coastline shapefile
#             clipped_coast = gpd.clip(full_coast, boundary_box).to_crs(utm_code)

#             # Clip the grid cells
#             cells_gdf.loc[:, "geometry"] = (
#                 cells_gdf["geometry"].difference(clipped_coast.geometry.union_all())
#             )

#             # Calculate area per cell
#             cells_gdf.loc[:, "area"] = cells_gdf.area

#             # Convert back to original projection and clip
#             clipped_cells_latlon = (
#                 gpd.clip(cells_gdf.to_crs(projection), boundary_box_unbuffered_gdf)
#                 .reset_index(drop=True)
#             )

#             # Initialize empty columns that can be added to later on
#             clipped_cells_latlon.loc[:, ["number_density_mean", "biomass_density_mean",
#                                          "abundance", "biomass"]] = 0.0

#             # Create output DataFrame
#             output_df = pd.DataFrame({
#                 "geometry": clipped_cells_latlon["geometry"].apply(lambda geom: geom.wkt)
#             })
#             # ---- Add the required columns
#             output_df = pd.concat([output_df, clipped_cells_latlon.loc[:, ["x", "y", "area"]]],
#                                   axis=1)
#             # ---- Initialize empty columns that can be added to later on
#             output_df.loc[:, ["number_density_mean", "biomass_density_mean", "abundance",
#                               "biomass"]] = 0.0

#             # Write to the database file (for the grid)
#             # ---- Create engine
#             engine = sqla.create_engine(f"sqlite:///{db_filepath}")
#             # ---- Connect and create table
#             _ = output_df.to_sql("grid_df", engine, if_exists="replace")

#             # Write to the database file (for the coastline shapefile)
#             # ---- Create output copy
#             coastline_out = pd.DataFrame({
#                 "geometry": clipped_coast_original["geometry"].apply(lambda geom: geom.wkt)
#             })
#             # ---- Concatenate
#             coastline_out = (
#                 pd.concat([coastline_out, clipped_coast_original.drop(columns="geometry")],
# axis=1)
#             )
#             # ---- Connect and create table
#             _ = coastline_out.to_sql("coastline_df", engine, if_exists="replace")

# ##################################################################################################
# # TEST: YAML FILE CONFIGURATION
# # ---- Define filepaths
# self = LiveSurvey
# live_init_config_path = "C:/Users/Brandyn/Documents/GitHub/echopop/config_files/live_initia
# lization_config.yml"
# live_file_config_path = "C:/Users/Brandyn/Documents/GitHub/echopop/config_files/live_survey_
# year_2019_config.yml"
# # ---- Run function: `live_configuration`
# file_configuration = self.config
# files = biology_files

# biology_output = initial_biology_output
# file_configuration = self.config
# table_name = "length_df"
# df = filtered_biology_output[table_name]
# database_file = biology_db
# kwargs = dict(dataframe=df, table_name=table_name, id_columns=["id"], primary_keys=["id"],
# output_type=pd.DataFrame)

# # NOTE: ARGUMENT: {working_dataset: Literal["acoustics", "biology"]}
# working_dataset = "acoustics"
# self = realtime_survey
# file_configuration = self.config
# self.results["biology"] = self.input["biology_processed"]
# self.results["acoustics"] = self.input["nasc_df"]

# # Get spatial column
# spatial_column = file_configuration["spatial_column"]

# # Initialize the working data dictionary
# working_data = copy.deepcopy(self.results)
# contrast_columns = []
# # ---- Define unique columns
# unique_columns = spatial_column + contrast_columns

# acoustic_db = file_configuration["database"][working_dataset]
# self = realtime_survey
# acoustic_dict = self.input["acoustics"]
# verbose = True
# contrast_columns = []
# db_file = acoustic_db
# table_name="survey_data_df"
# data_columns = data_columns
# unique_columns=unique_columns
# constraint="nasc > 0.0"
# data_dict = self.input["acoustics"]
# data_dict["nasc_df"]["stratum"] = 1
# data_dict["prc_nasc_df"]["stratum"] = 2
# table_name = "sigma_bs_mean_df"
# data_columns=["sigma_bs", "sigma_bs_count"]
# biology_db
# strata_df = self.input["spatial"]["strata"]

# def biology_pipeline(biology_dict: dict,
#                      strata_df: pd.DataFrame,
#                      file_configuration: dict,
#                      verbose: bool,
#                      contrast_columns: List[str] = []):

#     # Get spatial column
#     spatial_column = file_configuration["spatial_column"]
#     unique_columns = spatial_column + contrast_columns

#     # Get database file
#     acoustic_db = file_configuration["database"]["acoustics"]

#     # Get biology database file
#     biology_db = file_configuration["database"]["biology"]

#     # Check for data completion
#     # ---- List of boolean values
#     full_biology_data = (
#         [True for _, df in biology_dict.items() if isinstance(df, pd.DataFrame) and df is
#
# not None]
#     )
#     # ---- Validation
#     if not all(full_biology_data):
#         # ---- Print, if verbose
#         if verbose:
#             print(
#                 f"No new processed biology data available for processing."
#             )
#     else:
#         # Get related biology data
#         acoustic_df = get_nasc_sql_data(acoustic_db,
#                                         biology_dict,
#                                         unique_columns=unique_columns)

#         # Get the corresopding `sigma_bs` data (and also compute the s
# ample-number weighted average)
#         sigma_bs_df = get_sigma_bs_sql_data(acoustic_db,
#                                             biology_dict,
#                                             unique_columns=unique_columns)

#     # Calculate population estimates if valid data are available
#     if all([True if df is not None else False for df in [acoustic_df, sigma_bs_df]]):
#         # ---- Merge the NASC and sigma_bs datasets
#         nasc_biology = acoustic_df.merge(sigma_bs_df, on=unique_columns)
#         # ---- Compute the number densities (animals nmi^-2)
#         nasc_biology["number_density"] = (
#             nasc_biology["nasc"]
#             / (4.0 * np.pi * nasc_biology["sigma_bs_mean"])
#         )

#     # Get the corresponding average strata weights (computed for all fish)
#     weight_spatial_averages = get_average_strata_weights(biology_db,
#                                                          biology_dict,
#                                                          unique_columns=unique_columns)

#     if weight_spatial_averages is not None:
#         # Merge average weights with number density estimates
#         nasc_biology = nasc_biology.merge(weight_spatial_averages, on=unique_columns)

#         # Compute biomass densities
#         nasc_biology["biomass_density"] = (
#             nasc_biology["number_density"] * nasc_biology["average_weight"]
#         )

#     # Update the survey population estimate DataFrame with the newly computed densities
#     if not nasc_biology.empty:
#         sql_group_update(acoustic_db, dataframe=nasc_biology, table_name="survey_data_df",
#                         columns=["number_density", "biomass_density"],
#                         unique_columns=["stratum", "longitude", "latitude", "ping_time"])

#     # Summarize strata
#     summarize_strata(nasc_biology, strata_df, file_configuration)

# db_file=acoustic_db
# dataframe=nasc_biology
# table_name="survey_data_df"
# columns=["number_density", "biomass_density"]
# unique_columns=["stratum", "longitude", "latitude", "ping_time"]
# nasc_biology["number_density"].sum() / 2
# nasc_biology["number_density"]
# SQL(acoustic_db, "select", table_name="survey_data_df")
# SQL(biology_db, "select", table_name="strata_summary_df")
# strata_df = self.input["spatial"]["strata"].copy()
# strata_df[["length_mean", "weight_mean", "TS_mean", "number_density_mean",
#            "biomass_density_mean", "abundance_sum", "biomass_sum"]] = np.nan
# strata_df.drop(columns=["latitude_interval"], inplace=True)
# SQL(acoustic_db, "select", table_name="survey_data_df")

# SQL(biology_db, "drop", table_name="strata_summary_df")
# SQL(biology_db, "create", table_name="strata_summary_df", dataframe=strata_df,
# primary_keys=["stratum"])
# SQL(biology_db, "insert", table_name="strata_summary_df", dataframe=strata_df,
#     id_columns=["stratum"])

# tt = pd.DataFrame({
#     "x": np.array([1, 1, 1, 2, 2, 2, 3, 3, 3]),
#     "y": np.array([1, 2, 3, 1, 2, 3, 1, 2, 3]),
#     "area": 50 ** 2,
#     "mean_number_density": 0.0,
#     "mean_biomass_density": 0.0,
#     "abundance": 0.0,
#     "biomass": 0.0
# })

# nasc_biology_output_a = self.input["nasc_df"].assign(x=1, y=1).reset_index(drop=True)
# nasc_biology_output_a.loc[3, "x"] = 2
# nasc_biology_output_a.loc[3, "y"] = 3
# nasc_biology_output_a = nasc_biology_output_a.filter(["stratum", "x", "y", "longitude",
# "latitude", "nasc", "number_density", "biomass_density"])
# nasc_biology_output = nasc_biology_output_a.merge(sigma_bs_mean_df, on=spatial_column)
# nasc_biology_output["number_density"] = (
#     nasc_biology_output["nasc"]
#     / (4.0 * np.pi * nasc_biology_output["sigma_bs_mean"])
# )
# nasc_biology_output =nasc_biology_output.merge(general_weight_averages)
# nasc_biology_output["biomass_density"] = nasc_biology_output["number_density"]
# * nasc_biology_output["average_weight"]
# nasc_biology_output = nasc_biology_output.filter(["stratum", "x", "y", "longitude", "latitude"
# , "number_density", "biomass_density"])
# nasc_biology_output = nasc_biology_output[nasc_biology_output["number_density"] > 0.0]
# .reset_index()

# SQL(acoustic_db, "drop", table_name="reference")
# SQL(acoustic_db, "drop", table_name="grid")

# SQL(acoustic_db, "create", table_name = "reference", dataframe=tt)
# SQL(acoustic_db, "create", table_name = "grid", dataframe=nasc_biology_output_a)

# SQL(acoustic_db, "insert", table_name = "reference", dataframe=tt)
# SQL(acoustic_db, "insert", table_name = "grid", dataframe=nasc_biology_output_a)

# SQL(acoustic_db, "select", table_name="grid")
# SQL(acoustic_db, "select", table_name="reference")

# sql_group_update(acoustic_db, dataframe=nasc_biology_output,
#                  table_name="grid", columns=["number_density", "biomass_density"],
#                  unique_columns=["stratum", "x", "y", "longitude", "latitude"])

# SQL(acoustic_db, "select", table_name="grid")

# from typing import List

# data_table = "grid"
# grid_table = "reference"
# column_pairs = [("number_density", "abundance"), ("biomass_density", "biomass")]

# dataframe = nasc_biology_output

# import sqlalchemy as sqla

# grid_db_file = file_configuration["database"]["grid"]
# survey_db_file = Path(file_configuration["data_root_dir"]) / "database" / "acoustics.db"
# data_table = "survey_data_df"
# grid_table = "grid_df"
# coordinates = ["x", "y"]
# from echopop.live.sql_methods import SQL

# SQL(grid_db_file, "select", table_name=grid_table)
# SQL(survey_db_file, "select", table_name=data_table)
# SQL(data_table, "map")

# gridding_column = self.config["gridding_column"]

# updated_survey_data = nasc_biology.copy()
# # Get relevant table
# previous_grid = query_dataset(grid_db_file, updated_survey_data,
#                               table_name=grid_table,
#                               data_columns=["x", "y", "area", "number_density_mean",
#                                             "biomass_density_mean", "abundance", "biomass"],
#                               unique_columns=["x", "y"])
# previous_data = query_dataset(survey_db_file, updated_survey_data,
#                               table_name=data_table,
#                               data_columns=["x", "y", "number_density", "biomass_density"],
#                               unique_columns=["x", "y"])
# # Get unique coordinates
# update_keys = get_unique_identifiers(updated_survey_data, gridding_column).set_index(["x", "y"])


# # Index
# previous_grid.set_index(["x", "y"], inplace=True)
# previous_grid["biomass_density_mean"] = previous_data.groupby(["x", "y"])["biomass_density"]
# .mean()
# previous_grid["number_density_mean"] = previous_data.groupby(["x", "y"])["number_density"].mean()

# # Convert area from m^2 to nmi^2
# previous_grid["abundance"] = previous_grid["number_density_mean"] * previous_grid["area"]
# previous_grid["biomass"] = previous_grid["biomass_density_mean"] * previous_grid["area"]
# previous_grid = previous_grid.reset_index()

# sql_group_update(grid_db_file, dataframe=previous_grid,
#                  table_name=grid_table,
#                  columns=["number_density_mean", "biomass_density_mean", "abundance", "biomass"],
#                  unique_columns=["x", "y"])

# myrrh = SQL(grid_db_file, "select", table_name=grid_table)
# myrrh[myrrh.abundance > 0]

# update_keys["number_density_mean"] = updated_survey_data.groupby(["x", "y"])
# ["number_density"].mean()
# update_keys["biomass_density_mean"] = updated_survey_data.groupby(["x", "y"])
# ["biomass_density"].mean()

# am = SQL(grid_db_file, "select", table_name="grid_df")
# am[am.abundance > 0]
# bm = SQL(grid_db_file, "select", table_name="grid_df")
# bm[bm.abundance > 0]
# number_density_mean = updated_survey_data.groupby(["x", "y"])["number_density"].mean()
# biomass_density_mean = updated_survey_data.groupby(["x", "y"])["biomass_density"].mean()

# SQL(grid_db_file, "select", table_name=grid_table)


# pulled_data = pd.concat([SQL(grid_db_file, "select",
#                              table_name=grid_table,
#                              condition=f"x = {t[0]} & y = {t[1]}") for t in unique_coord])
# previous_cell_data = pd.concat([SQL(survey_db_file, "select",
#                                     table_name=data_table,
#                                     condition=f"x = {t[0]} & y = {t[1]}") for t in unique_coord])

# from typing import List

# from shapely.geometry import box

# from echopop.live.live_data_processing import (
#     get_average_strata_weights,
#     get_nasc_sql_data,
#     get_sigma_bs_sql_data,
#     summarize_strata,
# )
# from echopop.live.sql_methods import sql_group_update

# SQL(grid_db_file, "select", table_name="grid_df")
# # Compute means
# number_density_mean = previous_cell_data.groupby(["x", "y"])["number_density"].mean()
# previous_cell_data = previous_cell_data.groupby(["x", "y"])["biomass_density"].mean()

# [SQL(grid_db_file, "select", table_name=grid_table, condition=f"x =
# {xi} & y = {yi}") for xi, yi in zip(nasc_data_df["x"], nasc_data_df["y"])]

# # Write to the database file (for the grid)
# # ---- Create engine
# engine = sqla.create_engine(f"sqlite:///{db_filepath}")

# def update_population_grid(grid_db_file: str,
#                            data_table: str,
#                            grid_table: str,
#                            dataframe: pd.DataFrame,
#                            column_pairs: Union[List[tuple[str, str]], tuple[str, str]],
#                            coordinates: List[str]):

#     # Convert `column_pairs` to a list, if needed
#     if not isinstance(column_pairs, list):
#         column_pairs = [column_pairs]

#     dataframe[coordinates]
#     # Format the coordinate pairs
#     # ---- Convert coordinate values into a list of tuples
#     coord_pairs = [tuple(row) for row in dataframe[coordinates].itertuples(index=False)]
#     # ---- Get unique pairs
#     coords = list(set(coord_pairs))

#     # Format the SQL script command
#     # ---- Initialize
#     sql_script = []
#     # ---- Iteratively update
#     for input_column, output_column in column_pairs:
#         sql_script.append(
#         f"""
#         BEGIN TRANSACTION;

#         -- Calculate averages for input_column and update grid_table
#         WITH avgs AS (
#             SELECT
#                 {coordinates[0]},
#                 {coordinates[1]},
#                 AVG(d.{input_column}) as avg_value
#             FROM {data_table} d
#             GROUP BY d.{coordinates[0]}, d.{coordinates[1]}
#         )

#         -- Update the grid_table with both average and computed total
#         UPDATE {grid_table}
#         SET
#             mean_{input_column} = (
#                 SELECT avg_value
#                 FROM avgs
#                 WHERE avgs.{coordinates[0]} = {grid_table}.{coordinates[0]}
#                     AND avgs.{coordinates[1]} = {grid_table}.{coordinates[1]}
#             ),
#             {output_column} = (
#                 SELECT avg_value * {grid_table}.area
#                 FROM avgs
#                 WHERE avgs.{coordinates[0]} = {grid_table}.{coordinates[0]}
#                     AND avgs.{coordinates[1]} = {grid_table}.{coordinates[1]}
#             )
#         WHERE EXISTS (
#             SELECT 1
#             FROM avgs
#             WHERE avgs.{coordinates[0]} = {grid_table}.{coordinates[0]}
#               AND avgs.{coordinates[1]} = {grid_table}.{coordinates[1]}
#         );

#         COMMIT;
#         """
#         )

#     # Create the engine
#     engine = create_engine(f"sqlite:///{db_file}")

#     # Create the SQL database connection and send the script
#     with engine.connect() as connection:
#         dbapi_conn = connection.connection
#         _ = dbapi_conn.executescript("\n".join(sql_script))


# def update_population_grid(db_file: str,
#                            data_table: str,
#                            grid_table: str,
#                            dataframe: pd.DataFrame,
#                            column_pairs: Union[List[tuple[str, str]], tuple[str, str]],
#                            coordinates: List[str]):

#     # Convert `column_pairs` to a list, if needed
#     if not isinstance(column_pairs, list):
#         column_pairs = [column_pairs]

#     dataframe[coordinates]
#     # Format the coordinate pairs
#     # ---- Convert coordinate values into a list of tuples
#     coord_pairs = [tuple(row) for row in dataframe[coordinates].itertuples(index=False)]
#     # ---- Get unique pairs
#     coords = list(set(coord_pairs))

#     # Format the SQL script command
#     # ---- Initialize
#     sql_script = []
#     # ---- Iteratively update
#     for input_column, output_column in column_pairs:
#         sql_script.append(
#         f"""
#         BEGIN TRANSACTION;

#         -- Calculate averages for input_column and update grid_table
#         WITH avgs AS (
#             SELECT
#                 {coordinates[0]},
#                 {coordinates[1]},
#                 AVG(d.{input_column}) as avg_value
#             FROM {data_table} d
#             GROUP BY d.{coordinates[0]}, d.{coordinates[1]}
#         )

#         -- Update the grid_table with both average and computed total
#         UPDATE {grid_table}
#         SET
#             mean_{input_column} = (
#                 SELECT avg_value
#                 FROM avgs
#                 WHERE avgs.{coordinates[0]} = {grid_table}.{coordinates[0]}
#                     AND avgs.{coordinates[1]} = {grid_table}.{coordinates[1]}
#             ),
#             {output_column} = (
#                 SELECT avg_value * {grid_table}.area
#                 FROM avgs
#                 WHERE avgs.{coordinates[0]} = {grid_table}.{coordinates[0]}
#                     AND avgs.{coordinates[1]} = {grid_table}.{coordinates[1]}
#             )
#         WHERE EXISTS (
#             SELECT 1
#             FROM avgs
#             WHERE avgs.{coordinates[0]} = {grid_table}.{coordinates[0]}
#               AND avgs.{coordinates[1]} = {grid_table}.{coordinates[1]}
#         );

#         COMMIT;
#         """
#         )

#     # Create the engine
#     engine = create_engine(f"sqlite:///{db_file}")

#     # Create the SQL database connection and send the script
#     with engine.connect() as connection:
#         dbapi_conn = connection.connection
#         _ = dbapi_conn.executescript("\n".join(sql_script))


# SQL(acoustic_db, "select", table_name=data_table)
# SQL(acoustic_db, "select", table_name=grid_table)


# SQL(acoustic_db, "update", table_name="grid", dataframe=nasc_biology_output,
# unique_columns=["stratum", "x", "y"], columns=["number_density", "biomass_density"])
# SQL(acoustic_db, "select", table_name="reference")

# source_db = acoustic_db
# target_db = biology_db

# source_table = "grid"
# target_table = "strata_summary_df"

# data_columns = ["number_density", "biomass_density"]
# strata_columns = ["stratum"]
# strata = [2]
# stratum_list = ', '.join(map(str, stratum_values))

# data_column = data_columns[0]
# data_columns = data_columns[0]
# def sql_update_strata_summary(source_db: str,
#                               target_db: str,
#                               arg_fun: str,
#                               data_columns: List[tuple[str, str]],
#                               strata: list):

#     # Format strata list as a string
#     strata_str = ', '.join(map(str, strata))

#     # Function reference map
#     FUNCTION_MAP = {
#         "sum": {"function": "SUM",
#                 "suffix": "sum"},
#         "mean": {"function": "AVG",
#                 "suffix": "mean"}
#     }

#     # Prepare the SQL script
#     sql_script = f"""
#     -- Attach the source and target databases
#     ATTACH DATABASE '{source_db}' AS source;
#     ATTACH DATABASE '{target_db}' AS target;

#     """

#     # Dynamically format the cross-database command
#     for data_column, method in data_columns:
#         # ----- Format the function-method-suffic keys
#         suffix = FUNCTION_MAP[method]["suffix"]
#         fun = FUNCTION_MAP[method]["function"]
#         # ---- Create the combined SQL command using f-strings
#         sql_script += f"""
#         -- Calculate averages and directly update the target table
#         UPDATE target.{target_table}
#         SET {data_column}_{suffix} = (
#             SELECT {fun}({data_column})
#             FROM source.{source_table}
#             WHERE stratum = target.{target_table}.stratum
#         )
#         WHERE stratum IN ({strata_str});
#         """
#     # ----- Append DETACH commands only once at the end
#     sql_script += """
#     -- Detach the databases
#     DETACH DATABASE source;
#     DETACH DATABASE target;
#     """

#     # Create the engine
#     engine = create_engine(f"sqlite:///{target_db}")

#     # Create the SQL database connection and send the script
#     with engine.connect() as connection:
#         dbapi_conn = connection.connection
#         _ = dbapi_conn.executescript(sql_script)

# SQL(biology_db, "select", table_name=target_table)
# SQL(acoustic_db, "select", table_name=source_table)["number_density"].mean()
# connection.close()
# dbapi_conn.close()


# pairs = [(1, 2), (3, 4), (5, 6)]

# # Convert the pairs into a format suitable for SQL IN clause
# pairs_placeholder = ', '.join(f'({x}, {y})' for x, y in pairs)

# # Construct the SQL command as a text string
# sql_command = f'''
# BEGIN TRANSACTION;

# UPDATE reference
# SET total = (
#     SELECT AVG(g.sigma_bs) * r.area
#     FROM grid g
#     WHERE g.stratum = r.stratum_x
# )
# WHERE (stratum_x, stratum_y) IN ({pairs_placeholder});

# COMMIT;
# '''

# psi = 10 ** (-21/10)
# psi * 280**2 * 1500 * 128e-6 / 2
# psi / 3 * 280 ** 3 / 280 / 1852 ** 2 * nasc_biology["number_density"]

# psi * (280.0 ** 2) / 1852 ** 2
# depth_area = 280 ** 2 * psi
# swath_length = 0.5 * 1852
# depth_area * swath_length / 1852 ** 2 * nasc_biology["number_density"]
# 280 ** 2 * psi / 1852 ** 2 * nasc_biology["number_density"]

# SQL(acoustic_db, "map")
# beam_angle = 9.0 * np.pi / 180.0
# 280.0 * np.tan(beam_angle) * 2.0 * swath_length / 1852 ** 2 * nasc_biology["number_density"]
# 280.0 * np.tan(beam_angle) * 2.0 ** 2 * np.pi * swath_length / 1852 ** 2 *
# nasc_biology["number_density"]
# area = 2.0 * nasc_biology["center_of_mass"] ** 2 * np.tan(beam_angle)
# area / 1852 ** 2 * nasc_biology["number_density"]
# SQL(acoustic_db, "map")

# # Merge hake fraction data into `nasc_interval_df`
# # ---- Initial merge
# nasc_interval_df = nasc_interval_df.merge(
#     input_dict["spatial"]["strata_df"], on=[stratum_col, "haul_num"], how="outer"
# )
# # ---- Replace `fraction_hake` where NaN occurs
# nasc_interval_df["fraction_hake"] = nasc_interval_df["fraction_hake"].fillna(0.0)
# # ---- Drop NaN
# nasc_interval_df.dropna(subset=["transect_num"], inplace=True)

# # Calculate the along-transect number density (animals per nmi^2)
# # ---- Merge NASC measurements with mean sigma_bs for each stratum
# nasc_biology = nasc_interval_df.merge(sigma_bs_strata, on=[stratum_col])
# # ---- Calculate the number densities
# nasc_biology["number_density"] = (
#     nasc_biology["fraction_hake"]
#     * nasc_biology["nasc"]
#     / (4.0 * np.pi * nasc_biology["sigma_bs_mean"])
# )


# if working_dataset == "acoustic":
#     db_file = self.config["database"]["acoustic"]
# elif working_dataset == "biology":
#     db_file = self.config["database"]["biology"]
# else:
#     raise ValueError(
#         f"Argument for `working_dataset` [{working_dataset}] is invalid."
#         f" Value must either be 'acoustic' or 'biology'."
#     )

# # Extract the necessary correct strata mean sigma_bs
# sigma_bs_strata = analysis_dict["acoustics"]["sigma_bs"]["strata_mean_df"]

# # Pull out the length-weight conversion for each stratum
# length_weight_strata = analysis_dict["biology"]["weight"]["weight_stratum_df"]

# # Get the name of the stratum column
# stratum_col = settings_dict["transect"]["stratum_name"]


# catch_data = self.input["biology"]["catch_df"]

# # Get the spatial column name, if there is one
# spatial_column = file_configuration["spatial_column"]
# # ---- Append additional columns that will be used
# contrast_columns = spatial_column + ["sex", "species_id"]

# # Calculate grouped totals
# # ---- Sum the net haul weights from station 1/unaged fish
# catch_weights = catch_data.count_variable(
#     contrasts=["species_id"] + spatial_column,
#     variable="haul_weight", fun="sum"
# )
# # ---- Rename resulting columns for both
# catch_weights.rename(columns={"count": "total_weight"}, inplace=True)

# # ---- Specimen
# specimen_weights = specimen_weight_binned.sum().reset_index(name="total_weight")

# specimen_weight_binned
# # Calculate the sexed and total stratum weights for each sex among unaged fish
# # ---- Sum the net haul weights from station 1/unaged fish
# catch_weights = catch_data.count_variable(
#     contrasts=["species_id"] + file_configuration["spatial_column"],
#     variable="haul_weight", fun="sum"
# )
# # ---- Rename resulting columns for both
# catch_weights.rename(columns={"count": "total_weight"}, inplace=True)

# # For the specimen data
# # ---- Sum the net haul weights from station 1/unaged fish
# # ---- Specimen
# specimen_weights_sex = (
#     specimen_weight_binned
#     .groupby(contrast_columns)["weight"]
#     .sum()
# )
# # ---- Total (per stratum, if it exists)
# specimen_weight_total = specimen_weights_sex.transpose().unstack(1).sum(axis=1)

# # For the length (unaged) dataset
# length_weights_sex = (
#     length_weight_binned
#     .groupby(contrast_columns)["weight_interp"]
#     .sum()
# )
# # ---- Further reduce to the grand total (per stratum, if it exists)
# length_weight_total = length_weights_sex.transpose().unstack(1).sum(axis=1)

# # ---- Standardize the unaged sexed weights
# length_weight_standardized = (
#     (length_weights_sex / length_weight_total).unstack(0)
#     * catch_weights["total_weight"].to_numpy()
# )

# # Calculate the specimen weight proportions
# # ---- Pivot weight bins
# specimen_weight_binned_pvt = (
#     specimen_weight_binned.pivot_table(
#         columns=spatial_column,
#         index=["length_bin", "species_id", "sex"],
#         values="weight",
#         observed = False
#     )
# )
# # ---- Divide by the aged stratum weights (relative to only aged fish)
# specimen_weight_proportions_pvt = (
#     specimen_weight_binned_pvt / specimen_weight_total.to_numpy()
# )
# # ---- Pivot back to the desired format
# specimen_weight_proportion = (
#     specimen_weight_proportions_pvt
#     .stack().reset_index(name="weight_proportion")
#     .pivot_table(columns=stratum_column + ["species_id", "sex"],
#                  index="length_bin", values="weight_proportion")
# )
# # ---- Calculate the internal (i.e. only aged fish) for each sex
# within_specimen_sex_proportions = (
#     specimen_weight_proportion.sum()
# )

# # Calculate the total strata weights
# # ---- Index `catch_weights`
# catch_weights_idx = catch_weights.set_index(stratum_column + ["species_id"])
# # ---- Compute the spatially-stratified/grouped weights
# spatial_weights = (
#     pd.concat([specimen_weight_total.to_frame("total_weight"), catch_weights_idx])
#     .pivot_table(
#         columns=stratum_column,
#         aggfunc="sum",
#         values="total_weight",
#         observed=False
#     )
# )

# # Calculate the weight proportions relative to the overall stratum weights
# # ---- Aged
# # -------- Reformat into dataframe and merge with total stratum weights
# specimen_weights_binned_df = (
#     specimen_weight_binned_pvt.stack()
#     .to_frame("specimen_weight")
#     .reset_index()
#     .merge(spatial_weights.T.reset_index(), on=stratum_column)
# )
# # -------- Calculate proportions
# specimen_weights_binned_df["weight_proportion_overall"] = (
#     specimen_weights_binned_df["specimen_weight"] / specimen_weights_binned_df["total_weight"]
# )
# # -------- Consolidate to calculate the sexed proportions per stratum
# specimen_weight_sex_proportions = specimen_weights_binned_df.groupby(stratum_column
# + ["species_id", "sex"])[
#     "weight_proportion_overall"
# ].sum()
# # ---- Unaged
# # -------- Reformat into dataframe and merge with total stratum weights
# length_weights_sex_standardized_df = (
#     length_weight_standardized.stack()
#     .to_frame("catch_weight")
#     .reset_index()
#     .merge(spatial_weights.T.reset_index(), on=stratum_column)
# )
# # -------- Calculate proportions
# length_weights_sex_standardized_df["weight_proportion_overall"] = (
#     length_weights_sex_standardized_df["catch_weight"]
#     / length_weights_sex_standardized_df["total_weight"]
# )
# # -------- Back-calculate the sexed weight proportions relative to just unaged fish
# # ------------ Aggregate proportions
# length_total_sex_proportions = length_weights_sex_standardized_df.pivot_table(
#     columns=["species_id", "sex"], index=stratum_column, values="weight_proportion_overall"
# ).transpose().unstack(["species_id"]).sum(axis=0)
# # ------------ Re-compute the proportions
# length_weight_sex_proportions = (
#     length_weights_sex_standardized_df.pivot_table(
#         index=["species_id", "sex"], columns=stratum_column,
#         values="weight_proportion_overall"
#     )
#     / length_total_sex_proportions.to_numpy()
# )

# # Compute the overall length-binned weight distributions among unaged fish
# # ---- Extract the number proportions computed for unaged fish
# length_number_proportions = length_number_proportion.copy()
# # ---- Filter out values besides those computed for 'all' fish
# length_number_proportions = length_number_proportions[length_number_proportions["sex"] == "all"]
# # ---- Convert to a table
# length_number_proportions_tbl = length_number_proportions.pivot_table(
#     columns=stratum_column + ["species_id"],
#     index=["length_bin"],
#     values="proportion_number_length",
#     aggfunc="sum",
#     observed=False,
# )
# # ---- Extract the fitted weight values calculated for all fish
# length_weight_all = length_weight_df[length_weight_df["sex"] == "all"]
# # ---- Generate the fitted weight array
# fitted_weights = length_weight_all.copy()
# # ---- Get actual length bins in dataset
# fitted_weights = fitted_weights[fitted_weights["length_bin"].
# isin(length_number_proportions["length_bin"])]
# # ---- Apportion the averaged weights
# length_apportioned_weights = length_number_proportions_tbl.T * fitted_weights["weight_fitted"]
# .to_numpy()
# # ---- Compute the average weight proportions per length bin per stratum
# average_length_bin_weights = length_apportioned_weights.T / length_apportioned_weights
# .sum(axis=1)
# # ---- Convert back to a DataFrame
# average_length_bin_weights_df = average_length_bin_weights.unstack().reset_index(
#     name="weight_proportion"
# )

# # Calculate the aged and unaged weight proportions
# # ---- Aged
# aged_proportions = specimen_weight_sex_proportions.unstack("sex").sum(axis=1)
# # ---- Unaged
# unaged_proportions = 1 - aged_proportions
# # -------- Re-weight the unaged sexed proportions
# unaged_weight_sex_proportions_overall = (
#     (length_weight_sex_proportions * unaged_proportions.unstack().transpose()).astype(float).
# fillna(0.0)
# )

# unaged_proportions.unstack().transpose()
# # Format the outputs
# # ---- Aged: stratum-sex-age-length relative to aged and total weights
# aged_overall_df = (
#     specimen_weight_proportion.unstack()
#     .reset_index(name="weight_proportions")
#     .merge(
#         specimen_weights_binned_df[
#             stratum_column + ["length_bin", "sex", "species_id", "weight_proportion_overall"]
#         ]
#     )
# )
# # ---- Aged: stratum-sex relative to total weights
# aged_sex_df =within_specimen_sex_proportions.reset_index(name="weight_proportion_aged").set_index(
#         stratum_column + ["species_id", "sex"]
#     )
# # ---- Add the aged sex proportiosn relative to the overall survey
# aged_sex_df["weight_proportion_overall_aged"] = specimen_weight_sex_proportions
# # ---- Consolidate the aged and unaged sexed dataframes
# # -------- Initialize the dataframe
# aged_unaged_sex_proportions = aged_sex_df.reset_index().set_index(["species_id", "sex"]
# + stratum_column)
# # --------- Add the within-unaged weight proportions
# aged_unaged_sex_proportions["weight_proportion_unaged"] = (
#     length_weight_sex_proportions.stack()
# )
# # --------- Add the overall-unaged weight proportions
# aged_unaged_sex_proportions["weight_proportion_overall_unaged"] = (
#     unaged_weight_sex_proportions_overall.stack()
# )
# # ---- Overall aged and unaged proportions
# aged_unaged_proportions = aged_proportions.reset_index(name="aged_proportions")
# # ---- Set index
# aged_unaged_proportions.set_index(stratum_column + ["species_id"], inplace=True)
# # -------- Add unaged proportions
# aged_unaged_proportions["unaged_proportions"] = unaged_proportions#.reset_index()
# # ---- Reset the index
# aged_unaged_proportions = aged_unaged_proportions.reset_index()
# ##################################################################################################
# # * Functionality for reading in processed acoustic data
# # TODO: Expand data validator and limit cases to '*.zarr' (for now)
# # TODO: Refactor "extra" components such as the validation steps, xarray-to-dataframe piping, etc.
# # TODO: Documentation
# file_settings = file_configuration["input_directories"]["acoustics"]
# root_directory = file_configuration["data_root_dir"]


# ##################################################################################################
# def reset_db_files(file_configuration: dict, table_exception: Optional[Union[str,
# List[str]]] = None):

#     # Get all database files
#     database_files = file_configuration["database"]

#     # Iterate through all keys
#     for _, db_file in database_files.items():
#         # ---- Map the table names
#         table_names = SQL(db_file, "map")
#         # ---- Drop any noted exceptions
#         if not isinstance(table_exception, list):
#             table_exception = [table_exception]
#         # ---- Drop exception table name
#         if None not in table_exception:
#             table_names = list(set(table_names) - set(table_exception))
#         _ = [SQL(db_file, "drop", table_name=table) for table in table_names]
#         # ---- Validate that all tables were removed
#         if set(table_names).intersection(set(SQL(table_names, "map"))):
#             raise ValueError(
#                 f"Attempted reset of [{str(db_file)}] failed."
#             )

# SPATIAL_CONFIG_MAP = {
#     "closest_haul": {
#         "proximity": {
#             "choices": ["distance", "time"],
#         },
#     },
#     "global" : {},
#     "griddify": {
#         "bounds": {
#             "longitude": {
#                 "types": [float]
#             },
#             "latitude": {
#                 "types": [float]
#             },
#             "northings": {
#                 "types": [float]
#             },
#             "eastings": {
#                 "types": [float]
#             },
#             "pairs": [("longitude", "latitude"), ("northings", "eastings")],
#         },
#         "grid_resolution": {
#             "x_distance": {
#                 "types": float,
#             },
#             "y_distance": {
#                 "types": float,
#             },
#             "d_longitude": {
#                 "types": float,
#             },
#             "d_latitude": {
#                 "types": float,
#             },
#             "grid_size_x": {
#                 "types": int,
#             },
#             "grid_size_y": {
#                 "types": int,
#             },
#             "pairs": [("x_distance", "y_distance"), ("d_longitude", "d_latitude"),
#                       ("grid_size_x", "grid_size_y")],
#         },
#     },
#     "inpfc": {
#         "stratum_names": {
#                 "types": [int, str]
#             },
#         "latitude_max": {
#             "types": [float],
#         },
#     },
#     "weighted_haul": {
#         "proximity": {
#             "choices": ["distance", "time"]
#         },
#     },
# }


# reset_db_files(file_configuration, table_exception = "files_read")
# reset_db_files(file_configuration)

# stamp = 20240714194248
# stamp.astype(int)
# int(stamp)
# import re
# from datetime import datetime


# def infer_datetime_format(timestamp_str: Union[int, str]):
#     patterns = {
#         r"^\d{14}$": "%Y%m%d%H%M%S",             # YYYYMMDDHHMMSS
#         r"^\d{8}$": "%Y%m%d",                     # YYYYMMDD
#         r"^\d{6}$": "%H%M%S",                     # HHMMSS
#         r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$": "%Y-%m-%d %H:%M:%S",  # YYYY-MM-DD HH:MM:SS
#         r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}$": "%Y/%m/%d %H:%M:%S",  # YYYY/MM/DD HH:MM:SS
#         r"^\d{4}-\d{2}-\d{2}$": "%Y-%m-%d",       # YYYY-MM-DD
#         r"^\d{4}/\d{2}/\d{2}$": "%Y/%m/%d"        # YYYY/MM/DD
#     }

#     for pattern, date_format in patterns.items():
#         if re.match(pattern, timestamp_str):
#             return date_format

#     raise ValueError("Unknown timestamp format")

# filter_dict = dict(species_filer=species_filter, trawl_filter=trawl_filter)

# def biology_data_filter(biology_data: pd.DataFrame, filter_dict: dict):

#     # Create dataframe copy
#     data_copy = biology_data.copy()

#     # Iterate through dictionary to apply filters (if present)
#     for column, value in filter_dict.items():
#         if column in data_copy.columns:
#             data_copy = data_copy[data_copy[column] == value]

#     # Return output
#     return data_copy


# df[(df['species_id'] == species_filter if 'species_id' in df.columns else True)]
# df[(df["species_id"] == 17 if "species_id" in df.columns)]

# (df[df["haul_num"] == 17 if "haul_num" in df.columns] else True)


# from datetime import datetime

# df = biology_output["trawl_info_df"]
# df.loc[(df['species_id'] == species_filter if 'species_id' in df.columns else True), :]
# df.index

# biology_output["trawl_info_df"].reset_index().index
# df = biology_output["catch_df"]
# df = df.loc[0, :].to_frame().T
# df.index
# df.loc[(df['species_id'] == species_filter if 'species_id' in df.columns else True)]

# def convert_datetime(timestamp: Union[int, str, pd.Series]):

#     if isinstance(timestamp, pd.Series):
#         test_timestamp = str(timestamp[0])
#     else:
#         test_timestamp = str(timestamp)

#     # Approximate the datetime format
#     datetime_format = infer_datetime_format(str(test_timestamp))

#     #
#     if isinstance(timestamp, pd.Series):
#         return timestamp.apply(lambda x: datetime.strptime(x, datetime_format))
#     else:
#         return datetime.strptime(timestamp, datetime_format)

# infer_datetime_format(stamp)
# convert_datetime(stamp)
# infer_datetime_format(202407)

# # {'global': False, 'INPFC': True, 'closest_haul': False, 'weighted_haul': False}
# file_configuration["geospatial"]["link_biology_acoustics"] = "INPFC"
# file_configuration["geospatial"]
# spatial_config = file_configuration["geospatial"]
# ###############

# acoustic_data = self.input["acoustics"]
# biology_data = self.input["biology"]


# from echopop.live.live_core import SPATIAL_CONFIG_MAP


# def load_spatial_data(acoustic_data: dict,
#                       biology_data: dict,
#                       file_configuration: dict,):

#     # Extract spatial strata *only* if spatial information from the configuration settings
#     # ---- Get (geo)spatial config
#     spatial_config = file_configuration["geospatial"]
#     # ---- Remove case sensitivity
#     spatial_config = {key.lower(): value for key, value in spatial_config.items()}
#     # ---- Extract the projection
#     projection = spatial_config["projection"]
#     # ---- Extract the biology-acoustics linking method options
#     acoustics_biology_link = spatial_config["link_biology_acoustics"]

#     # Validate the configuration
#     validate_spatial_config(spatial_config)

#     # Create spatial dictionary that will be added as an `input`
#     spatial_dict = {"link_method": acoustics_biology_link}

#     # Assign the spatial link constraints to the acoustic and biological data
#     if acoustics_biology_link == "INPFC":
#         spatial_dict.update({"strata": create_inpfc_strata(spatial_config)})

#     # Return the dictionary as an output
#     return spatial_dict


#     # Convert the DataFrame to a GeoDataFrame
#     acoustic_data_gdf = gpd.GeoDataFrame(
#         data=acoustic_data,
#         geometry=gpd.points_from_xy(acoustic_data["longitude"], acoustic_data["latitude"]),
#         crs=projection
#     )

#     # Validate the spatial biology-acoustics linking method
#     # ---- Get the biology-acoustics linking method
#     link_method = next(key for key, value in acoustics_biology_link.items() if value)
#     # ---- Flag Error if unexpected method
#     if link_method not in ["global", "closest_haul", "INPFC", "weighted_haul"]:
#         raise ValueError(
#             f"Unexpected biology-acoustic linking parameter ([{link_method}]). Valid options "
#             f"include: 'global', 'closest_haul', 'weighted_haul', and 'INPFC'."
#         )

# ##################################################################################################
# # TEST: BIOLOGY FILE INGESTION CONFIGURATION
# # NOTE:
# # ---- Run function: `load_validated_acoustic_data` using previously defined `file_configuration`
# biology_data, file_configuration = load_biology_data(file_configuration)
# biology_data
# ##################################################################################################
# prc_nasc_df = acoustic_data["prc_nasc_df"]

# def process_acoustic_data(acoustic_data_df: pd.DataFrame, file_configuration: dict,
#                           echometrics: bool = True):

#     # Integrate NASC (and compute the echometrics, if necessary)
#     nasc_data_df = (
#         acoustic_data_df.groupby(["longitude", "latitude", "ping_time"])
#         .apply(lambda group: integrate_nasc(group, echometrics))
#         .reset_index()
#     )
#     # ---- Amend the dtypes if echometrics were computed
#     if echometrics:
#         nasc_data_df = (
#             nasc_data_df
#             .astype({"n_layers": int, "mean_Sv": float, "max_Sv": float, "nasc_db": float,
#                              "center_of_mass": float, "dispersion": float, "evenness": float,
#                              "aggregation": float, "occupied_area": float})
#         )

#     # Get the name of the associated db file
#     acoustics_db = file_configuration["database"]["acoustics"]
#     # ---- Get current tables
#     tables = SQL(acoustics_db, "inspect")

#     #
#     if "nasc_df" not in tables:
#         _ = SQL(acoustics_db, "insert", table_name="nasc_df", dataframe=nasc_data_df)
#     else:
#         # ----
#         nasc_sql = SQL(acoustics_db, "select", table_name="nasc_df")
#         # ----
#         index_equiv = nasc_data_df[["longitude", "latitude", "ping_time"]].isin(nasc_sql)
#         # ----
#         bool_idx = index_equiv.apply(lambda x: np.all(x), axis=1)
#         # ----
#         _ = SQL(acoustics_db, "insert", table_name="nasc_df",
# dataframe=nasc_data_df.loc[~bool_idx])
#         # ----
#         nasc_data_df = pd.concat([nasc_sql, nasc_data_df], ignore_index=True)

#     # Return the output
#     return nasc_data_df


# SQL(acoustics_db, command="drop", table_name="nasc_df")
# SQL(acoustics_db, "inspect")

# nasc_analysis = process_acoustic_data(acoustic_data["prc_nasc_df"], file_configuration)

# SQL(acoustics_db, command="select", table_name="nasc_df")

# TS_SLOPE = 20.0
# TS_INTERCEPT = -68.0

# # CONVERT TO TS
# comb_lengths["ts"] = TS_SLOPE * np.log10(comb_lengths["length"]) + TS_INTERCEPT
# # TO SIGMA_BS
# comb_lengths["sigma_bs"] = 10 ** (comb_lengths["ts"] / 10)
# # WEIGHTED MEAN SIGMA_BS
# sigma_mean = np.average(comb_lengths["sigma_bs"], weights=comb_lengths["length_count"])

# from typing import Optional

# from echopop.acoustics import to_dB, to_linear, ts_length_regression
# from echopop.utils import operations

# __all__ = ["operations"]

# # Meld bio datasets
# length_datasets = biology_data["specimen_df"].meld(biology_data["length_df"],
#                                                    contrasts=["haul_num", "sex",
# "species_id", "length"])

# # Create distribution
# distrib_params = file_configuration["biology"]["length_distribution"]["bins"]

# length_bins = np.linspace(**{key: value for key, value in zip(["start", "stop", "num"],
# distrib_params)}, dtype=float)
# binwidth = np.diff(length_bins / 2.0).mean()
# intervals = np.concatenate([length_bins[:1] - binwidth, length_bins + binwidth])
# length_bins_df = pd.DataFrame({"bin": length_bins, "interval": pd.cut(length_bins, intervals)})
# #
# length_datasets["length_bin"] = pd.cut(length_datasets["length"], bins=intervals,
# labels=length_bins_df["bin"])

# stratify_key = file_configuration["geospatial"]["link_biology_acoustics"]

# if stratify_key == "global":
#     length_distribution = (
#         length_datasets.pivot_table(columns=["sex"], index=["length_bin"],
#                                     values="length_count", aggfunc="sum", observed=False)
#     )
#     #
#     length_distribution["total"] = length_distribution.sum(axis=1)

# length_distribution.transpose()
# SQL(biology_db, "drop", table_name="length_distribution")
# # Get the name of the associated db file
# biology_db = file_configuration["database"]["biology"]
# # ---- Get current tables
# tables = SQL(biology_db, "inspect")


# if "length_distribution" not in tables:
#     _ = SQL(biology_db, "insert", table_name="length_distribution",
#             dataframe=length_distribution.transpose())


# SQL(biology_db, "select", table_name="length_distribution")
# SQL(biology_db, "drop", table_name="length_distribution")
# SQL(biology_db, "replace", table_name="length_distribution",
# dataframe=length_distribution.unstack().reset_index(name="count"))
# length_distribution.unstack().reset_index(name="count")
# mixed = SQL(biology_db, "select", table_name="length_distribution")
# length_bins[:1]
# from typing import Optional

# from echopop.acoustics import to_dB, to_linear, ts_length_regression
# from echopop.utils import operations

# __all__ = ["operations"]

# biology_data = self.input["biology"]

# # Meld bio datasets
# length_datasets = biology_data["specimen_df"].meld(biology_data["length_df"],
#                                                    contrasts=["haul_num", "species_id", "length"])

# ts_length_parameters_spp = [
#     spp
#     for spp in file_configuration["acoustics"]["TS_length_regression_parameters"].values()
#     if spp["number_code"] in np.unique(length_datasets.species_id).astype(int)
# ]

# # ---- get species info
# target_species = pd.DataFrame.from_dict(ts_length_parameters_spp)

# ts_lengths_df = length_datasets.merge(
#     target_species.drop("length_units", axis=1),
#     left_on=["species_id"],
#     right_on=["number_code"],
# )
# # ---- filter out other spp
# length_datasets[length_datasets["species_id"].isin(target_species["number_code"])]

# #
# file_configuration["acoustics"]["TS_length_regression_parameters"][target_species["text_code"]]

# def average_sigma_bs(length: Union[pd.DataFrame, float, int],
#                      TS_L_slope: Optional[float] = None,
#                      TS_L_intercept: Optional[float] = None,
#                      weighted: Optional[Union[float, int, str]] = None):

#     #
#     if isinstance(length, pd.DataFrame):
#         if "length" not in length.columns:
#             raise ValueError(
#                 "Column [`length`] missing from dataframe input `length`."
#             )
#         if "TS_L_slope" not in length.columns and TS_L_slope is None:
#             raise ValueError(
#                 "Value [`TS_L_slope`] missing from dataframe input `length` and optional "
#                 "separate argument `TS_L_slope`."
#             )
#         if "TS_L_intercept" not in length.columns and TS_L_intercept is None:
#             raise ValueError(
#                 "Value [`TS_L_intercept`] missing from dataframe input `length` and optional "
#                 "separate argument `TS_L_intercept`."
#         )
#     elif isinstance(length, float) or isinstance(length, int):
#         if TS_L_slope is None:
#             raise ValueError(
#                 "Argument [`TS_L_slope`] missing."
#             )
#         elif TS_L_slope is not None and not isinstance(TS_L_slope, float):
#             raise TypeError(
#                 "Argument `TS_L_slope` must be type `float`."
#         )
#         if "TS_L_intercept" not in length.columns and TS_L_intercept is None:
#             raise ValueError(
#                 "Argument [`TS_L_intercept`] missing."
#         )
#         elif TS_L_intercept is not None and not isinstance(TS_L_intercept, float):
#             raise TypeError(
#                 "Argument `TS_L_intercept` must be type `float`."
#         )

#     #
#     if TS_L_slope is None:
#         TS_L_slope = length["TS_L_slope"]

#     #
#     if TS_L_intercept is None:
#         TS_L_intercept = length["TS_L_intercept"]

#     #
#     if isinstance(length, pd.DataFrame):
#         length_val = length["length"]

#     ts_value = ts_length_regression(length_val, TS_L_slope, TS_L_intercept)
#     sigma_bs_value = to_linear(ts_value)


#     if isinstance(weighted, str):
#         if weighted not in length.columns:
#             raise ValueError(
#                 f"Argument [`weighted` (str)], '{weighted}', is not a column in argument
# `length` "
#                 f"(DataFrame)."
#             )
#         else:
#             return (sigma_bs_value * length[weighted]).sum() / length[weighted].sum()
#     elif weighted is not None:
#         if weighted.size != sigma_bs_value.size:
#             raise ValueError(
#                 f"Argument [`weighted` (float|int)] of size {weighted.size} does not
# match size of "
#                 f"argument [`length` (float|int)`] of size {sigma_bs_value.size}."
#             )
#         else:
#             return (sigma_bs_value * weighted).sum() / weighted.sum()
#     else:
#         return sigma_bs_value.mean()

# def parse_condition(condition):
#     # Handle nested conditions and logical operators
#     condition = condition.replace('&', ' AND ').replace('|', ' OR ')

#     # Handle "IN" lists and replace square brackets with parentheses
#     condition = re.sub(r'(\w+)\s*IN\s*\[(.*?)\]', lambda m: f"{m.group(1)} IN ({m.group(2)})",
# condition, flags=re.IGNORECASE)

#     # Handle range conditions for BETWEEN, including floats
#     condition = re.sub(r'(\d*\.\d+|\d+)\s*<=\s*(\w+)\s*<=\s*(\d*\.\d+|\d+)',
#                        lambda m: f"{m.group(2)} BETWEEN {m.group(1)} AND {m.group(3)}", condition)

#     # Handle individual comparisons
#     condition = re.sub(r'(\w+)\s*([<>!=]+)\s*(\d*\.\d+|\d+)', lambda m: f"{m.group(1)}
# {m.group(2)} {m.group(3)}", condition)
#     condition = re.sub(r'(\w+)\s*([<>!=]+)\s*(\'[^\']*\')', lambda m: f"{m.group(1)}
# {m.group(2)} {m.group(3)}", condition)

#     # Handle single equal sign
#     condition = re.sub(r'(\w+)\s*=\s*(\d*\.\d+|\d+)', lambda m: f"{m.group(1)} = {m.group(2)}",
# condition)

#     # Remove redundant spaces
#     condition = re.sub(r'\s+', ' ', condition).strip()

#     return condition

# ##################################################################################################
# def load_spatial_data(file_configuration: dict,
#                       acoustic_data: pd.DataFrame,
#                       coordinate_metadata: xr.Dataset):

#     # Extract spatial strata *only* if spatial information from the configuration settings
#     # ---- Extract the projection
#     projection = file_configuration["geospatial"]["projection"]
#     # ---- Extract the biology-acoustics linking method options
#     acoustics_biology_link = file_configuration["geospatial"]["link_biology_acoustics"]

#     # Convert the DataFrame to a GeoDataFrame
#     acoustic_data_gdf = gpd.GeoDataFrame(
#         data=acoustic_data,
#         geometry=gpd.points_from_xy(acoustic_data["longitude"], acoustic_data["latitude"]),
#         crs=projection
#     )

#     # Validate the spatial biology-acoustics linking method
#     # ---- Get the biology-acoustics linking method
#     link_method = next(key for key, value in acoustics_biology_link.items() if value)
#     # ---- Flag Error if unexpected method
#     if link_method not in ["global", "closest_haul", "INPFC", "weighted_haul"]:
#         raise ValueError(
#             f"Unexpected biology-acoustic linking parameter ([{link_method}]). Valid options "
#             f"include: 'global', 'closest_haul', 'weighted_haul', and 'INPFC'."
#         )

#     # Create INPFC stratum dataframe
#     # ---- Extract

#     # Validate projection information
#     # ---- Create a dummy GeoDataFrame to extract CRS information
#     # geo_crs = gpd.GeoDataFrame(geometry=[], crs=projection)
#     # ---- Extract coordinate limits from the acoustic data
#     # lat_min = coordinate_metadata.attrs['geospatial_lat_min']
#     # lat_max = coordinate_metadata.attrs['geospatial_lat_max']
#     # lon_min = coordinate_metadata.attrs['geospatial_lon_min']
#     # lon_max = coordinate_metadata.attrs['geospatial_lon_max']
#     # # ---- Create boundary box string
#     # boundary_box_str = (
#     #     f"POLYGON(({lon_min} {lat_min}, {lon_max} {lat_min}, {lon_max} {lat_max}, "
#     #     f"{lon_min} {lat_max}, {lon_min} {lat_min}))"
#     # )

#     # data_gdf = gpd.GeoDataFrame(acoustic_data, geometry=gpd.points_from_xy(
# acoustic_data["longitude"], acoustic_data["latitude"]),crs=f"epsg:{
# utm_string_generator(lon_min, lat_min)}")
#     # gpd.GeoDataFrame(acoustic_data, geometry=gpd.points_from_xy(acoustic_data["longitude"],
# acoustic_data["latitude"]),crs=f"epsg:4326").to_crs("epsg:32610")

#     # from pyproj import CRS
#     # from pyproj.aoi import AreaOfInterest
#     # from pyproj.database import query_utm_crs_info

#     # utm_crs_list = query_utm_crs_info(
#     #     datum_name="WGS 84",
#     #     area_of_interest=AreaOfInterest(
#     #         west_lon_degree=lon_min,
#     #         south_lat_degree=lat_min,
#     #         east_lon_degree=-lon_max,
#     #         north_lat_degree=lat_max,
#     #     ),
#     # )
#     # CRS.from_epsg(utm_crs_list[0].code).to_epsg("+proj=latlon")

# ##################################################################################################
# def live_data(file_configuration: dict):

#     # Extract the file directories (or from the configuration) containing acoustic, biological,and
#     # spatial definitions/data/parameters
#     # ---- Acoustic data
#     acoustic_data = load_validated_acoustic_data(file_configuration)
#     # ---- Biological data
#     # ---- Spatial data


# ##################################################################################################
# # * Define `LIVE_DATA_STRUCTURE` configuration mapping (this will be in an equivalent `core.py`)
# # TODO: Update structure with additional information (as needed)
# # TODO: Documentation
# LIVE_DATA_STRUCTURE = {
#     "meta": {
#         "provenance": dict(),
#         "date": list(),
#     },
#     "input": {
#         "acoustics": {
#             "nasc_df": pd.DataFrame(),
#         },
#         "biology": {
#             "catch_df": pd.DataFrame(),
#             "distributions": {
#                 "length_bins_df": pd.DataFrame(),
#             },
#             "length_df": pd.DataFrame(),
#             "specimen_df": pd.DataFrame(),
#         },
#     },
#     "results": {
#         "acoustics": dict(),
#         "biology": dict(),
#         "stratified": dict(),
#     },
# }
# ##################################################################################################
# # * Define `LiveSurvey` class structure
# # TODO: Incorporate validators
# # TODO: Scope out full structure including accessors, attributes, and methods
# # TODO: Configure input arguments (for initialization)
# # TODO: Documentation
# class LiveSurvey:
#     """
#     A real-time processing version of the `echopop` base `Survey` class that ingests biological,
#     acoustic, and event meta data to provide population estimates when generated.
#     """

#     def __init__(
#         self,
#         live_init_config_path: Union[str, Path],
#         live_file_config_path: Union[str, Path],
#     ):
#         # Initialize `meta` attribute
#         self.meta = copy.deepcopy(LIVE_DATA_STRUCTURE["meta"])

#         # Loading the configuration settings and definitions that are used for defining the
#         # configuration settings
#         self.config = live_configuration(live_file_config_path, live_file_config_path)

#         # Loading the datasets defined in the configuration files
#         self.input = el.load_survey_data(self.config)

#         # Initialize the `results` data attribute
#         self.results = copy.deepcopy(LIVE_DATA_STRUCTURE["results"])

# current_units = zarr_data_ds["frequency_nominal"].units
# acoustic_analysis_settings["transmit"]
# file_configuration

# specimen_df = pd.DataFrame(
#     {
#         "haul_num": np.repeat([1,2,3], 4),
#         "station": "specimen",
#         "sex": np.tile(["male", "female"], 6),
#         "length": np.array([11, 11, 11, 18, 21, 23, 13, 11, 19, 25, 18, 9]),
#         "weight": np.array([11, 14, 16, 18, 21, 23, 13, 11, 19, 25, 18, 9]) / 3.5,
#     },
# )

# length_df = pd.DataFrame(
#     {
#         "haul_num": np.repeat([1,2,3], 4),
#         "station": "length",
#         "sex": np.tile(["male", "female"], 6),
#         "length": np.array([16, 15, 19, 14, 9, 10, 18, 15, 16, 22, 17, 11]),
#         "length_count": np.array([103, 123, 257, 106, 52, 329, 131, 72, 101, 212, 93, 81]),
#     },
# )

# catch_df = pd.DataFrame(
#     {
#         "haul_num": np.array([1, 2, 3]),
#         "weight": np.array([503.12, 684.32, 978.54])
#     }
# )

# TS_SLOPE = 20.0
# TS_INTERCEPT = -68.0

# acoustic_db = realtime_survey.config["database"]["acoustics"]
# SQL(acoustic_db, "select", table_name="files_processed")
# biology_db = realtime_survey.config["database"]["biology"]
# SQL(biology_db, "select", table_name="files_processedk")
# ####
# # CONCATENATE FILE SOURCES
# specimen_reframed = specimen_df.groupby(["haul_num", "station", "sex", "length"])["length"].val
# ue_counts().to_frame("length_count").reset_index()
# specimen_reframed
# # MELD
# all_lengths = pd.concat([length_df, specimen_reframed])
# # COMBINE
# comb_lengths = all_lengths.groupby(["haul_num", "sex", "length"])["length_count"].sum().to_fra
# me("length_count").reset_index()


# from echopop.live.sql_methods import SQL

# # Assuming that you have a LiveSurvey object defined
# # ---- Get the database file name (and path)
# biology_db = livesurvey_object.config["database"]["biology"]
# # ----
# # CONVERT TO TS
# comb_lengths["ts"] = TS_SLOPE * np.log10(comb_lengths["length"]) + TS_INTERCEPT
# # TO SIGMA_BS
# comb_lengths["sigma_bs"] = 10 ** (comb_lengths["ts"] / 10)
# # WEIGHTED MEAN SIGMA_BS
# sigma_mean = np.average(comb_lengths["sigma_bs"], weights=comb_lengths["length_count"])

# # INTEGRATE NASC
# path2file = "C:/Users/15052/Downloads/win_1720457505_1720460000_NASC.zarr"

# Path(path2file).exists()
# xds = xr.open_dataset(path2file, engine="zarr")
# xds
# xdf = xds.to_dataframe().reset_index()
# xdf["NASC"] = xdf["NASC"].fillna(0.0)
# # convert frequency
# xdf["frequency_nominal"] = (xdf["frequency_nominal"] * 1e-3).astype(int)
# # filter
# xdf_38 = xdf[xdf["frequency_nominal"] == nasc_frequency]

# xdf_38.plot.scatter(x="distance", y="depth", c="NASC")
# plt.show()

# xdf_int = xdf_38.groupby(["distance", "longitude", "latitude"])["NASC"].sum().reset_index()

# plt.scatter(xdf_int["longitude"], xdf_int["latitude"], c=xdf_int["NASC"])
# plt.plot(xdf_int["longitude"], xdf_int["latitude"])
# plt.show()

# # CONVERT TO NUMBER DENSITY
# xdf_int["number_density"] = xdf_int["NASC"] / (4.0 * np.pi * sigma_mean)


# import geopandas as gpd
# import pyproj

# ###################
# from geopy.distance import distance
# from shapely.geometry import Point, Polygon, box
# from shapely.ops import unary_union

# grid_settings = file_configuration["geospatial"]["griddify"]
# grid = []
# lat_step = distance(nautical=grid_settings["grid_resolution"]["x"]).meters
# lon_step = distance(nautical=grid_settings["grid_resolution"]["y"]).meters
# lat_min = grid_settings["bounds"]["latitude"][0]
# lat_max = grid_settings["bounds"]["latitude"][1]
# lon_min = grid_settings["bounds"]["longitude"][0]
# lon_max = grid_settings["bounds"]["longitude"][1]

# utm_str = utm_string_generator((lon_max + lon_min)/2, (lat_max + lat_min)/2)
# utm_proj = pyproj.Proj(f"epsg:{utm_str}")
# x_min, y_min = utm_proj(lon_min, lat_min)
# x_max, y_max = utm_proj(lon_max, lat_max)

# lat = 55.5000
# lon = -134.2500
# utm_code = int(utm_string_generator(lon, lat))
# utm_proj = pyproj.Proj(f"epsg:{utm_code}")
# utm_proj(lon, lat)
# gpd.GeoDataFrame(geometry=gpd.points_from_xy(np.array([lon]), np.array([lat])), crs=project
# ion).to_crs(utm_code)


# num_lon_steps = int((x_max - x_min) / lon_step)
# num_lat_steps = int((y_max - y_min) / lat_step)

# lon1 = np.linspace(x_min, x_max - lon_step, num_lon_steps)
# lat1 = np.linspace(y_min, y_max - lat_step, num_lat_steps)
# lon2 = lon1 + lon_step
# lat2 = lat1 + lat_step

# # Convert UTM coordinates back to degrees
# lon_min_grid, lat_min_grid = np.meshgrid(lon1, lat1)
# lon_max_grid, lat_max_grid = np.meshgrid(lon2, lat2)

# # Convert UTM coordinates back to degrees with adjusted resolution
# lon1_deg, lat1_deg = utm_proj(lon_min_grid.ravel(), lat_min_grid.ravel(), inverse=True)
# lon2_deg, lat2_deg = utm_proj(lon_max_grid.ravel(), lat_max_grid.ravel(), inverse=True)


# polygons = [box(lon1, lat1, lon2, lat2) for lon1, lat1, lon2, lat2 in zip(lon1_deg, lat1_deg, lo
# n2_deg, lat2_deg)]
# grid_gdf = gpd.GeoDataFrame({'geometry': polygons}, crs="epsg:4326")


# world = gpd.read_file("C:/Users/15052/Documents/GitHub/echopop_data/live_2019_files/coastline/
# ne_110m_land/ne_110m_land.shp")
# bbox = box(lon_min - 0.25, lat_min - 0.25, lon_max + 0.25, lat_max + 0.25)
# shapefile = world
# clipped_shapefile = gpd.clip(shapefile, bbox).to_crs(utm_proj.srs)
# clipped_shapefile.to_crs(utm_proj.srs)
# # clipped_geometry = bbox.intersection(world.union_all())
# # clipped_gdf = gpd.GeoDataFrame(geometry=[clipped_geometry], crs=world.crs)

# from shapely.geometry import MultiPolygon

# # Create an empty list to store clipped geometries
# # clipped_geometries = []

# # # Iterate over each grid polygon
# # for index, row in grid_gdf.iterrows():
# #     # Intersect grid polygon with land shape
# #     intersection = row['geometry'].intersection(clipped_shapefile.unary_union)

# #     # If intersection is a MultiPolygon, get the difference with the land shape
# #     if isinstance(intersection, MultiPolygon):
# #         clipped = row['geometry'].difference(clipped_shapefile.unary_union)
# #         if clipped.is_empty:
# #             continue
# #         clipped_geometries.append(clipped)
# #     else:
# #         # If intersection is a single Polygon, directly add to clipped geometries
# #         clipped_geometries.append(intersection)

# # clipped_grid = gpd.GeoDataFrame(geometry=clipped_geometries, crs=grid_gdf.crs)

# clipped_geometries = grid_gdf['geometry'].to_crs(utm_proj.srs).difference(clipped_shapefile
# .geometry.union_all())
# clipped_gdf = gpd.GeoDataFrame(geometry=clipped_geometries)
# clipped_gdf.to_crs(epsg=32610)

# invalid_geometries = clipped_gdf[~clipped_gdf.is_valid]
# clipped_gdf = clipped_gdf.buffer(0.001)
# clipped_gdf['area_sqm'] = clipped_gdf.area / 46300.00000000001**2

# clipped_gdf.area

# fig, ax = plt.subplots(figsize=(10, 8))
# clipped_gdf.plot(ax=ax, facecolor="none", edgecolor="black")
# clipped_shapefile.plot(ax=ax, edgecolor='black', linewidth=0.5)
# plt.tight_layout()
# plt.show()


# bbox.crs = {"init": "epsg:4326"}
# intersection = gpd.overlay(bbox, world, how='intersection')

# world_cut = gpd.sjoin(world, gpd.GeoDataFrame(geometry=[bbox]), how='inner', op='intersects')

# world_cut = world[world.geometry.intersects(bbox)]
# world_cut.to_crs("epsg:4326")

# import matplotlib.pyplot as plt

# fig, ax = plt.subplots(figsize=(10, 10))
# grid_gdf.plot(ax=ax, facecolor="none", edgecolor="black")
# world_cut.plot(ax=ax, linewidth=2, color='blue')
# plt.show()

# for cell in grid_gdf:

#     x, y = cell.exterior.xy  # Extract x and y coordinates of the cell
#     ax.fill(x, y, facecolor='none', edgecolor='black')  # Plot the cell as a polygon patch
# # Plot coastline
# # world.plot(ax=ax, linewidth=2, color='blue')
# plt.show()


# bbox = (lat_min, lon_min, lat_max, lon_max)
# G = ox.graph_from_bbox(bbox[2], bbox[3], bbox[0], bbox[1], network_type='none', simplify=False)
# G = ox.geometries_from_bbox(north=bbox[2], south=bbox[0], east=bbox[3], west=bbox[1],
# tags={'natural': ['coastline']})


# latitudes = range(int(lat_min), int(lat_max) + 1, int(lat_step))
# longitudes = range(int(lon_min), int(lon_max) + 1, int(lon_step))

# # Initialize `meta` attribute
# meta = copy.deepcopy(LIVE_DATA_STRUCTURE["meta"])

# # Loading the configuration settings and definitions that are used to
# # initialize the Survey class object
# config = yaml.safe_load(Path(initialization_config).read_text())

# nasc_frequency = config["acoustics"]["nasc_frequency"]
