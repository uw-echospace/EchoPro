from pathlib import Path
from typing import List, Union

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely.geometry
import sqlalchemy as sqla
from geopy.distance import distance
from shapely.geometry import box

from ..spatial.projection import utm_string_generator
from .sql_methods import query_dataset, sql_group_update


def create_inpfc_strata(spatial_config: dict):

    # Extract the INPFC definitions
    inpfc_definitions = spatial_config["inpfc"]

    # Create latitude bins
    latitude_bins = np.concatenate([[-90.0], inpfc_definitions["latitude_max"], [90.0]])
    # ---- Append 1 more stratum layer
    bin_names = np.concatenate(
        [inpfc_definitions["stratum_names"], [np.max(inpfc_definitions["stratum_names"]) + 1]]
    )

    # Create spatial key
    inpfc_strata_df = pd.DataFrame(
        {
            "latitude_limit": np.concatenate([inpfc_definitions["latitude_max"], [90.0]]),
            "latitude_interval": pd.cut(
                np.concatenate([inpfc_definitions["latitude_max"], [90.0]]), latitude_bins
            ),
            "stratum": bin_names,
        }
    )

    # Add boundaries
    # ---- Lower
    inpfc_strata_df["lower"] = inpfc_strata_df["latitude_interval"].apply(lambda x: x.left)
    # ---- Upper
    inpfc_strata_df["upper"] = inpfc_strata_df["latitude_interval"].apply(lambda x: x.right)

    # Return the dataframe
    return inpfc_strata_df


def apply_inpfc_definitions(dataset: pd.DataFrame, inpfc_df: pd.DataFrame):

    # Create dataset copy
    dataset = dataset.copy()

    # Bin the data based on latitude
    if isinstance(dataset, pd.DataFrame) and "latitude" in dataset.columns:
        dataset.loc[:, "stratum"] = pd.cut(
            dataset.loc[:, "latitude"],
            np.unique(np.hstack([inpfc_df.loc[:, "lower"], inpfc_df.loc[:, "upper"]])),
            labels=inpfc_df.loc[:, "stratum"],
        ).astype(int)

        return dataset
    else:
        strata = pd.cut(
            dataset.copy(),
            np.unique(np.hstack([inpfc_df.loc[:, "lower"], inpfc_df.loc[:, "upper"]])),
            labels=inpfc_df.loc[:, "stratum"],
        ).astype(int)

        return strata

    # Return the INPFC-stratified dataset
    # return dataset


def apply_spatial_definitions(dataset: Union[dict, pd.Series], spatial_dict: dict):

    # Get the acoustic-biology link method
    link_method = spatial_dict["link_method"]

    # Apply spatial definitions
    if isinstance(dataset, dict) and link_method == "INPFC":
        dataset.update(
            {k: apply_inpfc_definitions(d, spatial_dict["strata"]) for k, d in dataset.items()}
        )
    elif isinstance(dataset, pd.Series) and link_method == "INPFC":
        return apply_inpfc_definitions(dataset, spatial_dict["strata"])


# def apply_inpfc_definitions(acoustic_data: dict, biology_data: dict, spatial_config: dict):

#     # Extract the INPFC definitions
#     inpfc_definitions = spatial_config["inpfc"]

#     # Create latitude bins
#     latitude_bins = np.concatenate([[-90.0], inpfc_definitions["latitude_max"], [90.0]])
#     # ---- Append 1 more stratum layer
#     bin_names = np.concatenate([inpfc_definitions["stratum_names"],
#                                 [np.max(inpfc_definitions["stratum_names"]) + 1]])

#     # Create spatial key
#     spatial_config["spatial_key"] = pd.DataFrame({
#         "latitude_limit": inpfc_definitions["latitude_max"],
#     })
#     # ---- Cut
#     spatial_config["spatial_key"]["stratum"] = (
#         pd.cut(inpfc_definitions["latitude_max"],
#                latitude_bins,
#                right = True,
#                labels = bin_names)
#     )

#     # Get the `prc_nasc_df` values, if they exist, and apply stratification information
#     if not acoustic_data["prc_nasc_df"].empty:
#         # ---- Bin the latitude data
#         acoustic_data["prc_nasc_df"]["stratum"] = pd.cut(
#             acoustic_data["prc_nasc_df"]["latitude"],
#             latitude_bins,
#             right = True,
#             labels = bin_names,
#         )

#     # Get the `trawl_info_df` values, if they exist, and apply stratification information
#     if not biology_data["trawl_info_df"].empty:
#         # ---- Bin the latitude data
#         biology_data["trawl_info_df"]["stratum"] = pd.cut(
#             biology_data["trawl_info_df"]["latitude"],
#             latitude_bins,
#             right = True,
#             labels = bin_names,
#         )


def define_boundary_box(boundary_dict: dict, projection: str):

    # Get x-coordinates
    if "longitude" in boundary_dict.keys():
        x = np.array(boundary_dict["longitude"])
    else:
        x = np.array(boundary_dict["northings"])

    # Get y-coordinates
    if "latitude" in boundary_dict.keys():
        y = np.array(boundary_dict["latitude"])
    else:
        y = np.array(boundary_dict["eastings"])

    # Create a boundary DataFrame
    bound_df = pd.DataFrame(
        {
            "x": np.array([x.min(), x.max(), x.max(), x.min(), x.min()]),
            "y": np.array([y.min(), y.max(), y.max(), y.min(), y.min()]),
        }
    )

    # Convert to a GeoDataFrame and return the GeoDataFrame
    return gpd.GeoDataFrame(
        data=bound_df,
        geometry=gpd.points_from_xy(bound_df["x"], bound_df["y"]),
        crs=projection,
    )


def apply_griddify_definitions(dataset: pd.DataFrame, spatial_config: dict):

    # Extract the griddification definitions
    griddify_definitions = spatial_config["griddify"]

    # Get the projection definition
    projection = spatial_config["projection"]

    # Compute the boundary box GeoDataFrame
    boundary_box = define_boundary_box(griddify_definitions["bounds"], projection)

    # Convert the coordinates, if needed
    if not set(["northings", "eastings"]).intersection(set(griddify_definitions["bounds"].keys())):
        # ---- Compute the equivalent UTM string
        utm_num = int(
            utm_string_generator(
                np.median(boundary_box.loc[0:3, "x"]), np.median(boundary_box.loc[0:3, "y"])
            )
        )
        # ---- Compute the boundary box GeoDataFrame with the new projection
        boundary_box = boundary_box.to_crs(utm_num)
        # ---- Create a new projection for later
        projection_new = f"epsg:{utm_num}"
    else:
        projection_new = projection

    # Define the step sizes
    # ---- Define x step size
    x_step = distance(nautical=griddify_definitions["grid_resolution"]["x_distance"]).meters
    # ---- Define y step size
    y_step = distance(nautical=griddify_definitions["grid_resolution"]["y_distance"]).meters

    # Get the boundary tuple
    xmin, ymin, xmax, ymax = boundary_box.total_bounds

    # Generate the cells
    grid_cells = []
    # ---- Iterate through
    for y0 in np.arange(ymin, ymax, y_step):
        for x0 in np.arange(xmin, xmax, x_step):
            x1 = x0 - x_step
            y1 = y0 + y_step
            grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))

    # Convert to a GeoDataFrame
    cells_gdf = gpd.GeoDataFrame(grid_cells, columns=["geometry"], crs=projection_new)

    # Get the centroids
    cells_gdf["cell_centroid"] = cells_gdf["geometry"].centroid

    # Convert to GeoDataFrame
    dataset_gdf = gpd.GeoDataFrame(
        data=dataset,
        geometry=gpd.points_from_xy(dataset["longitude"], dataset["latitude"]),
        crs=projection,
    )
    # ---- To UTM
    dataset_gdf = dataset_gdf.to_crs(projection_new)

    # Extract x- and y-coordinates
    dataset_gdf["x"] = dataset_gdf["geometry"].x
    dataset_gdf["y"] = dataset_gdf["geometry"].y

    # Bin the longitude data
    dataset_gdf["stratum_x"] = pd.cut(
        dataset_gdf["x"],
        np.arange(xmin, xmax + x_step, x_step),
        right=False,
        labels=np.arange(1, len(np.arange(xmin, xmax + x_step, x_step))),
    ).astype(int)

    # Bin the latitude data
    dataset_gdf["stratum_y"] = (
        pd.cut(
            dataset_gdf["y"],
            np.arange(ymin, ymax + y_step, y_step),
            right=True,
            labels=range(len(np.arange(ymin, ymax + y_step, y_step)) - 1),
        ).astype(int)
        + 1
    )

    # Update the original dataset
    return dataset_gdf.loc[:, ["stratum_x", "stratum_y"]].rename(
        columns={"stratum_x": "x", "stratum_y": "y"}
    )
    # dataset.loc[:, "x"] = dataset_gdf.copy().loc[:, "stratum_x"]
    # dataset.loc[:, "y"] = dataset_gdf.copy().loc[:, "stratum_y"]


# def apply_griddify_definitions(acoustic_data: dict, biology_data: dict, spatial_config: dict):

#     # Extract the griddification definitions
#     griddify_definitions = spatial_config["griddify"]

#     # Get the projection definition
#     projection = spatial_config["projection"]

#     # Compute the boundary box GeoDataFrame
#     boundary_box = define_boundary_box(griddify_definitions["bounds"], projection)

#     # Convert the coordinates, if needed
#    if not set(["northings", "eastings"]).intersection(set(griddify_definitions["bounds"].keys())):
#         # ---- Compute the equivalent UTM string
#         utm_num = int(utm_string_generator(np.median(boundary_box.loc[0:3, "x"]),
#                                            np.median(boundary_box.loc[0:3, "y"])))
#         # ---- Compute the boundary box GeoDataFrame with the new projection
#         boundary_box = boundary_box.to_crs(utm_num)
#         # ---- Create a new projection for later
#         projection_new = f"epsg:{utm_num}"
#     else:
#         projection_new = projection

#     # Define the step sizes
#     # ---- Define x step size
#     x_step = distance(nautical=griddify_definitions["grid_resolution"]["x_distance"]).meters
#     # ---- Define y step size
#     y_step = distance(nautical=griddify_definitions["grid_resolution"]["y_distance"]).meters

#     # Get the boundary tuple
#     xmin, ymin, xmax, ymax = boundary_box.total_bounds

#     # Generate the cells
#     grid_cells = []
#     # ---- Iterate through
#     for y0 in np.arange(ymin, ymax+y_step, y_step):
#         for x0 in np.arange(xmin, xmax+x_step, x_step):
#             x1 = x0-x_step
#             y1 = y0+y_step
#             grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))

#     # Convert to a GeoDataFrame
#     cells_gdf = gpd.GeoDataFrame(grid_cells, columns=["geometry"], crs=projection_new)

#     # Get the centroids
#     cells_gdf["cell_centroid"] = cells_gdf["geometry"].centroid

#     # Get the `prc_nasc_df` values, if they exist, and apply stratification information
#     if not acoustic_data["prc_nasc_df"].empty:

#         #
#         prc_nasc_df = acoustic_data["prc_nasc_df"]

#         # to GDF
#         prc_nasc_gdf = gpd.GeoDataFrame(
#             data=prc_nasc_df,
#             geometry=gpd.points_from_xy(prc_nasc_df["longitude"], prc_nasc_df["latitude"]),
#             crs=projection,
#         )
#         # to UTM
#         prc_nasc_new = prc_nasc_gdf.to_crs(projection_new)

#         prc_nasc_new["x"] = prc_nasc_new["geometry"].x
#         prc_nasc_new["y"] = prc_nasc_new["geometry"].y

#         # ---- Bin the latitude data
#         prc_nasc_new["stratum_x"] = pd.cut(
#             prc_nasc_new["x"],
#             np.arange(xmin, xmax+x_step, x_step),
#             right = True,
#             labels = range(len(np.arange(xmin, xmax+x_step, x_step)) - 1),
#         ).astype(int) + 1

#         prc_nasc_new["stratum_y"] = pd.cut(
#             prc_nasc_new["y"],
#             np.arange(ymin, ymax+y_step, y_step),
#             right = True,
#             labels = range(len(np.arange(ymin, ymax+y_step, y_step)) - 1),
#         ).astype(int) + 1

#         #
#         acoustic_data["prc_nasc_df"]["stratum"] = (
#             prc_nasc_new["stratum_x"].astype(str) + "-" + prc_nasc_new["stratum_y"].astype(str)
#         )

#     if not biology_data["trawl_info_df"].empty:

#         #
#         trawl_info_df = biology_data["trawl_info_df"]

#         # to GDF
#         trawl_info_gdf = gpd.GeoDataFrame(
#             data=trawl_info_df,
#             geometry=gpd.points_from_xy(trawl_info_df["longitude"], trawl_info_df["latitude"]),
#             crs=projection,
#         )
#         # to UTM
#         trawl_info_new = trawl_info_gdf.to_crs(projection_new)

#         trawl_info_new["x"] = trawl_info_new["geometry"].x
#         trawl_info_new["y"] = trawl_info_new["geometry"].y

#         # ---- Bin the latitude data
#         trawl_info_new["stratum_x"] = pd.cut(
#             trawl_info_new["x"],
#             np.arange(xmin, xmax+x_step, x_step),
#             right = True,
#             labels = range(len(np.arange(xmin, xmax+x_step, x_step)) - 1),
#         ).astype(int) + 1

#         trawl_info_new["stratum_y"] = pd.cut(
#             trawl_info_new["y"],
#             np.arange(ymin, ymax+y_step, y_step),
#             right = True,
#             labels = range(len(np.arange(ymin, ymax+y_step, y_step)) - 1),
#         ).astype(int) + 1

#         #
#         biology_data["trawl_info_df"]["stratum"] = (
#            trawl_info_new["stratum_x"].astype(str) + "-" + trawl_info_new["stratum_y"].astype(str)
#         )


def initialize_grid(file_configuration=dict):

    # Get root directory, if defined
    if "data_root_dir" in file_configuration:
        # root_dir = Path(file_configuration["data_root_dir"])
        root_dir = file_configuration["data_root_dir"]
    else:
        # root_dir = Path()
        root_dir = ""

    # Get `grid` settings
    grid_database = file_configuration["input_directories"]["grid"]["database_name"]
    # ----
    db_directory = Path(file_configuration["database_directory"])
    # db_directory = file_configuration["database_directory"]

    # Create full filepath
    # db_filepath = root_dir / "database" / grid_database
    db_filepath = db_directory / grid_database
    # db_filepath = "/".join([db_directory, grid_database])
    # ---- Update config
    file_configuration["database"]["grid"] = db_filepath

    # Create if file doesn't already exist
    if not db_filepath.exists():

        # Get projection
        projection = file_configuration["geospatial"]["projection"]

        # Get grid settings
        grid_settings = file_configuration["geospatial"]["griddify"]

        # Get the resolution
        resolution = grid_settings["grid_resolution"]
        # ---- Convert from nmi to m
        resolution_m = {key: distance(nautical=dist).meters for key, dist in resolution.items()}

        # Get boundary coordinates
        boundary = grid_settings["bounds"]
        # ---- x
        x = boundary["longitude"]
        # ---- y
        y = boundary["latitude"]
        # ---- Create DataFrame
        boundary_df = pd.DataFrame(
            {
                "x": np.array([np.min(x), np.max(x), np.max(x), np.min(x), np.min(x)]),
                "y": np.array([np.min(y), np.min(y), np.max(y), np.max(y), np.min(y)]),
            }
        )

        # Create GeoDataFrame
        boundary_gdf = gpd.GeoDataFrame(
            data=boundary_df,
            geometry=gpd.points_from_xy(boundary_df["x"], boundary_df["y"]),
            crs=projection,
        )

        # Convert to UTM (decimal degrees to m)
        # ---- Create UTM code
        utm_code = utm_string_generator(
            (boundary_df.x.min() + boundary_df.x.max()) / 2,
            (boundary_df.y.min() + boundary_df.y.max()) / 2,
        )
        # ---- Create number code
        utm_num = int(utm_code)
        # ---- UTM conversion
        boundary_gdf_utm = boundary_gdf.to_crs(utm_num)

        # Get step sizes for each grid cell
        # ---- x
        x_step = resolution_m["x_distance"]
        # ---- y
        y_step = resolution_m["y_distance"]

        # Prepare grid cell generation
        # ---- Get new boundaries
        xmin, ymin, xmax, ymax = boundary_gdf_utm.total_bounds
        # ---- Initialize empty list
        grid_cells = []
        # ---- Initialize coordinate counter
        y_ct = 0
        x_coord = []
        y_coord = []
        # ---- Iterate through to generate cells
        for y0 in np.arange(ymin, ymax, y_step):
            y_ct += 1
            x_ct = 0
            for x0 in np.arange(xmin, xmax, x_step):
                x_ct += 1
                # ---- Step forward
                x_coord.append(x_ct)
                y_coord.append(y_ct)
                x1 = x0 - x_step
                y1 = y0 + y_step
                # ---- Append to list
                grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))

        # Convert to a GeoDataFrame
        cells_gdf = gpd.GeoDataFrame(grid_cells, columns=["geometry"], crs=utm_code)
        # ---- Add coordinates
        cells_gdf.loc[:, "x"] = np.array(x_coord)
        cells_gdf.loc[:, "y"] = np.array(y_coord)

        # Get coastline shapefile directory, if defined
        if "coastline" in file_configuration["input_directories"]:

            # Get coastline settings
            coast_settings = file_configuration["input_directories"]["coastline"]
            # ---- Get root folder directory
            # coast_root = root_dir / coast_settings["directory"] / coast_settings["coastline_name"]
            coast_root = "/".join(
                [root_dir, coast_settings["directory"], coast_settings["coastline_name"]]
            )
            # ---- Create filepath
            shp_filepath = (
                # root_dir / coast_settings["directory"]
                # / coast_settings["coastline_name"]
                # coast_root
                # / f"{coast_settings['coastline_name']}.shp"
                "/".join([coast_root, f"{coast_settings['coastline_name']}.shp"])
            )
            # ---- Validate existence
            # if not shp_filepath.exists():
            #     raise FileNotFoundError(
            #         f"{shp_filepath} does not exist!"
            #     )

            # Get original lat/lon geometry boundaries
            xmin0, ymin0, xmax0, ymax0 = boundary_gdf.total_bounds

            # Read in file
            full_coast = gpd.read_file(
                shp_filepath,
                engine="pyogrio",
                storage_options=file_configuration["storage_options"],
            )
            # ---- Convert to UTM
            full_coast_utm = full_coast.to_crs(utm_code)
            # ---- Remove empty
            full_coast_utm = full_coast_utm[~full_coast_utm.is_empty]

            # Create bounding box with a buffer
            boundary_box = box(xmin0 - 5, ymin0 - 5, xmax0 + 5, ymax0 + 5)
            # ---- Create an unbuffered copy
            boundary_box_unbuffered = box(xmin0, ymin0, xmax0, ymax0)
            # ---- Convert to a GeoDataFrame
            boundary_box_unbuffered_gdf = gpd.GeoDataFrame(
                geometry=[boundary_box_unbuffered], crs=projection
            )
            # ---- Clip the coastline for saving
            clipped_coast_original = gpd.clip(
                full_coast, box(xmin0 + 1, ymin0 + 1, xmax0 + 1, ymax0 + 1)
            )

            # Clip the coastline shapefile
            clipped_coast = gpd.clip(full_coast, boundary_box).to_crs(utm_code)

            # Clip the grid cells
            cells_gdf.loc[:, "geometry"] = cells_gdf["geometry"].difference(
                clipped_coast.geometry.union_all()
            )

            # Calculate area per cell
            cells_gdf.loc[:, "area"] = cells_gdf.area
            # ---- Convert back to nmi^2 from m^2
            cells_gdf.loc[:, "area"] = cells_gdf.loc[:, "area"] / 1852**2

            # Convert back to original projection and clip
            clipped_cells_latlon = gpd.clip(
                cells_gdf.to_crs(projection), boundary_box_unbuffered_gdf
            ).reset_index(drop=True)

            # Initialize empty columns that can be added to later on
            clipped_cells_latlon.loc[
                :, ["number_density_mean", "biomass_density_mean", "abundance", "biomass"]
            ] = 0.0

            # Create output DataFrame
            output_df = pd.DataFrame(
                {"geometry": clipped_cells_latlon["geometry"].apply(lambda geom: geom.wkt)}
            )
            # ---- Add the required columns
            output_df = pd.concat(
                [output_df, clipped_cells_latlon.loc[:, ["x", "y", "area"]]], axis=1
            )
            # ---- Initialize empty columns that can be added to later on
            output_df.loc[
                :, ["number_density_mean", "biomass_density_mean", "abundance", "biomass"]
            ] = 0.0

            # Write to the database file (for the grid)
            # ---- Create engine
            engine = sqla.create_engine(f"sqlite:///{db_filepath}")
            # ---- Connect and create table
            _ = output_df.to_sql("grid_df", engine, if_exists="replace", index=False)

            # Write to the database file (for the coastline shapefile)
            # ---- Create output copy
            coastline_out = pd.DataFrame(
                {"geometry": clipped_coast_original["geometry"].apply(lambda geom: geom.wkt)}
            )
            # ---- Concatenate
            coastline_out = pd.concat(
                [coastline_out, clipped_coast_original.drop(columns="geometry")], axis=1
            )
            # ---- Connect and create table
            _ = coastline_out.to_sql("coastline_df", engine, if_exists="replace", index=False)


def update_population_grid(
    file_configuration: dict, coordinates: Union[List[str], str], dataset: Union[dict, pd.DataFrame]
):

    # Extract input directory settings
    file_settings = file_configuration["input_directories"]

    # Get filepath for grid
    grid_db = list(
        Path(file_configuration["database_directory"]).glob(
            pattern=f"{file_settings['grid']['database_name']}"
        )
    )[0]

    # Get filepath for acoustics
    survey_db = list(
        Path(file_configuration["database_directory"]).glob(
            pattern=f"{file_settings['acoustics']['database_name']}"
        )
    )[0]

    # Define the SQL tables that will be parsed and queries
    data_table = "survey_data_df"
    grid_table = "grid_df"

    # Get indexed survey data
    indexed_data = query_dataset(
        survey_db,
        dataset,
        table_name=data_table,
        data_columns=coordinates + ["x", "y", "number_density", "biomass_density"],
        unique_columns=coordinates,
    )

    # Get indexed grid data
    indexed_grid = query_dataset(
        grid_db,
        indexed_data,
        table_name=grid_table,
        data_columns=[
            "x",
            "y",
            "area",
            "number_density_mean",
            "biomass_density_mean",
            "abundance",
            "biomass",
        ],
        unique_columns=["x", "y"],
    )

    # Set DataFrame index
    indexed_grid.set_index(["x", "y"], inplace=True)

    # Update the areal density estimates
    # ---- Number (animals/nmi^2)
    indexed_grid["number_density_mean"] = indexed_data.groupby(["x", "y"])["number_density"].mean()
    # ---- Bioamss (kg/nmi^2)
    indexed_grid["biomass_density_mean"] = indexed_data.groupby(["x", "y"])[
        "biomass_density"
    ].mean()

    # Compute the abundance and biomass per grid cell
    # ---- Abundance (# animals)
    indexed_grid["abundance"] = indexed_grid["number_density_mean"] * indexed_grid["area"]
    # ---- kg
    indexed_grid["biomass"] = indexed_grid["biomass_density_mean"] * indexed_grid["area"]

    # Update grid table
    # ---- Reset index
    output_df = indexed_grid.reset_index()
    # ---- Grouped update
    sql_group_update(
        grid_db,
        dataframe=output_df,
        table_name=grid_table,
        columns=["number_density_mean", "biomass_density_mean", "abundance", "biomass"],
        unique_columns=["x", "y"],
    )
