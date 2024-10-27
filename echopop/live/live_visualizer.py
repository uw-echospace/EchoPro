from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from shapely import wkt

from echopop.live.sql_methods import SQL


def plot_livesurvey_grid(
    grid_db: Union[Path, pd.DataFrame],
    projection: str,
    coast_db: Optional[Union[Path, pd.DataFrame]] = None,
):

    # Extract grid data from database if needed
    if isinstance(grid_db, Path):
        # ---- SELECT
        grid_data = SQL(grid_db, "select", table_name="grid_df")
    elif not isinstance(grid_db, pd.DataFrame):
        raise TypeError(
            "Grid data input (`grid_data`) must either be a `Path` or `pandas.DataFrame` object."
        )
    else:
        grid_data = grid_db

    # Extract coast data from database if needed
    if isinstance(coast_db, Path):
        # ---- SELECT
        coast_data = SQL(coast_db, "select", table_name="coastline_df")
    elif coast_data is None:
        # ---- SELECT from `grid_data`
        coast_data = SQL(grid_db, "select", table_name="coastline_df")
    elif not isinstance(coast_db, pd.DataFrame):
        raise TypeError(
            "Coast data input (`coast_data`) must either be a `Path` or `pandas.DataFrame` object, "
            "or exist within the SQL database as a table (`'coastline_df'`) within the `grid_data` "
            "input (i.e. `grid_data.db`)."
        )
    else:
        coast_data = coast_db

    # Format columns if needed (well-known-text to Polygon)
    # ---- `grid_data`
    if isinstance(grid_data["geometry"][0], str):
        grid_data["geometry"] = grid_data["geometry"].apply(wkt.loads)
    # ---- `coastline_data`
    if isinstance(coast_data["geometry"][0], str):
        coast_data["geometry"] = coast_data["geometry"].apply(wkt.loads)

    # Generate GeoDataFrames
    # ---- `grid`
    grid_gdf = gpd.GeoDataFrame(grid_data, geometry="geometry", crs=projection)
    # ---- `coast`
    coast_gdf = gpd.GeoDataFrame(coast_data, geometry="geometry", crs=projection)

    # Get appropriate plot axis-limits
    axis_limits = grid_gdf.total_bounds

    # Variable label dictionary map
    VARIABLE_MAP = {
        "number_density_mean": {
            "name": "Mean number density",
            "units": "Number of fish per $\\mathregular{nmi^2}$",
            "colormap": "cividis",
            "color_threshold": {"minimum": 1e1, "maximum": 1e6},
        },
        "biomass_density_mean": {
            "name": "Mean biomass density",
            "units": "kg $\\mathregular{nmi^{-2}}$",
            "colormap": "magma",
            "color_threshold": {"minimum": 1e1, "maximum": 1e6},
        },
        "abundance": {
            "name": "Abundance",
            "units": "Number of fish",
            "colormap": "viridis",
            "color_threshold": {
                "minimum": 1e1 * grid_gdf["area"].max(),
                "maximum": 1e6 * grid_gdf["area"].max(),
            },
        },
        "biomass": {
            "name": "Biomass",
            "units": "kg",
            "colormap": "plasma",
            "color_threshold": {
                "minimum": 1e1 * grid_gdf["area"].max(),
                "maximum": 1e6 * grid_gdf["area"].max(),
            },
        },
    }

    # Create a figure and a 2x2 grid of subplots
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))

    # List of variables to plot
    variables = list(VARIABLE_MAP.keys())

    # Iterate through and plot all subplots
    for ax, var in zip(axes.flat, variables):
        # ---- Get the colormap
        colormap = plt.colormaps.get_cmap(VARIABLE_MAP[var]["colormap"]).resampled(256)
        # ---- Invert
        newcolors = colormap(np.linspace(0, 1, 256))  # [::-1]
        # ---- Define `white`
        white = np.array([1, 1, 1, 1])
        # ---- Replace "start" color
        newcolors[0, :] = white
        # ---- Create the new custom colormap
        custom_cmap = ListedColormap(newcolors)
        # ---- Drop "empty" values
        sub_grid_gdf = grid_gdf[grid_gdf[var] > 0.0]
        if "color_threshold" in VARIABLE_MAP[var].keys():
            min_value = VARIABLE_MAP[var]["color_threshold"]["minimum"]
            max_value = VARIABLE_MAP[var]["color_threshold"]["maximum"]
        else:
            min_value = sub_grid_gdf[var].min()
            max_value = sub_grid_gdf[var].max()
        # ---- Normalize colorscale
        norm = plt.Normalize(vmin=min_value, vmax=max_value)
        # ---- Plot the polygons with color fills based on the variable (non-zero)
        grid_gdf.plot(
            column=var,
            ax=ax,
            edgecolor="gainsboro",
            legend=False,
            cmap=custom_cmap,
            norm=norm,
            markersize=0,
            linewidth=0.5,
        )
        # ---- Add coastline data layer
        coast_gdf.plot(ax=ax, linewidth=1.2, color="gray", edgecolor="black")
        # ---- Set axis limits
        ax.set_xlim(axis_limits[0] * 1.005, axis_limits[2] * 1.01)
        ax.set_ylim(axis_limits[1] * 0.98, axis_limits[3] * 1.005)
        # ---- Trim down the margins
        ax.margins(0, 0)
        # ---- Set adjustable aspect ratio
        # ax.set_aspect('equal', adjustable='box')
        # ---- Set the title and labels
        var_info = VARIABLE_MAP[var]
        ax.set_title(f"{var_info['name']}")
        # ---- Set axis labels
        ax.set_xlabel("Longitude (\u00B0E)")
        ax.set_ylabel("Latitude (\u00B0N)")
        # ---- Add colorbar
        sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
        sm._A = []  # fake up the array of the scalar mappable
        cbar = fig.colorbar(sm, ax=ax, shrink=0.5)
        cbar.set_label(f"{var_info['units']}")
        # ---- Add scalebar
        scalebar_length = 250  # Length of scale bar in km
        scalebar_length_in_degrees = scalebar_length / 111  # Assuming 1 degree = 111 km
        # ---- Transform scale bar coordinates to axis units
        # scalebar_x = axis_limits[0]*1.005 + (axis_limits[2]*1.01 - axis_limits[0]*1.005) * 0.1
        # scalebar_y = axis_limits[1]*0.98 + (axis_limits[3]*1.005 - axis_limits[1]*0.98) * 0.1
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        x_scale = (x1 - x0) * 0.1
        y_scale = (y1 - y0) * 0.1
        # scalebar_y_offset = (axis_limits[3]*1.005 - axis_limits[1]*0.98) * 0.05
        # ---- Plot scalebar
        # ax.plot([scalebar_x, scalebar_x + scalebar_length / 100],
        #         [scalebar_y, scalebar_y], color='black', lw=2)
        ax.plot(
            [x0 + x_scale, x0 + x_scale + scalebar_length_in_degrees],
            [y0 + y_scale, y0 + y_scale],
            color="black",
            lw=2,
        )
        # ---- Add scale text
        ax.text(
            x0 + x_scale + scalebar_length_in_degrees / 2,
            y0 + y_scale - (y1 - y0) * 0.025,
            f"{scalebar_length} km",
            ha="center",
            va="top",
            color="black",
        )

        # ax.text(scalebar_x + (scalebar_length / 200),
        #         scalebar_y - scalebar_y_offset,
        #         f'{scalebar_length} km', ha='center', va='bottom', color='black')

    # Adjust layout
    plt.tight_layout()

    # Show the plot
    # plt.show()
    return fig


def plot_livesurvey_track(
    survey_data_db: Union[Path, pd.DataFrame],
    projection: str,
    coast_db: Optional[Union[Path, pd.DataFrame]] = None,
):

    # Extract grid data from database if needed
    if isinstance(survey_data_db, Path):
        # ---- SELECT
        survey_data = SQL(survey_data_db, "select", table_name="survey_data_df")
    elif not isinstance(survey_data_db, pd.DataFrame):
        raise TypeError(
            "Grid data input (`grid_data`) must either be a `Path` or `pandas.DataFrame` object."
        )
    else:
        survey_data = survey_data_db

    # Extract coast data from database if needed
    if isinstance(coast_db, Path):
        # ---- SELECT
        coast_data = SQL(coast_db, "select", table_name="coastline_df")
    elif not isinstance(coast_db, pd.DataFrame):
        raise TypeError(
            "Coast data input (`coast_data`) must either be a `Path` or `pandas.DataFrame` object."
        )
    else:
        coast_data = coast_db

    # Format columns if needed (well-known-text to Polygon)
    # ---- `coastline_data`
    if isinstance(coast_data["geometry"][0], str):
        coast_data["geometry"] = coast_data["geometry"].apply(wkt.loads)

    # Generate GeoDataFrames
    # ---- `grid`
    survey_gdf = gpd.GeoDataFrame(
        survey_data,
        geometry=gpd.points_from_xy(survey_data["longitude"], survey_data["latitude"]),
        crs=projection,
    )
    # ---- `coast`
    coast_gdf = gpd.GeoDataFrame(coast_data, geometry="geometry", crs=projection)

    # Get appropriate plot axis-limits
    axis_limits = survey_gdf.total_bounds

    # Variable label dictionary map
    VARIABLE_MAP = {
        "nasc": {
            "name": "Nautical area scattering coefficient",
            "units": "$\\mathregular{m^{2}~nmi^{-2}}$",
            "colormap": "YlOrRd",
            "minimum": 0.0,
            "cbar_reverse": False,
            "color_threshold": {"minimum": 1e2, "maximum": 1e4},
            "size": [25, 150],
        },
        "number_density": {
            "name": "Mean number density",
            "units": "Number of fish per $\\mathregular{nmi^2}$",
            "colormap": "Purples",
            "minimum": 0.0,
            "cbar_reverse": False,
            "color_threshold": {
                "minimum": 1e1,
                "maximum": 1e6,
            },
            "size": [25, 150],
        },
        "biomass_density": {
            "name": "Mean biomass density",
            "units": "kg $\\mathregular{nmi^{-2}}$",
            "colormap": "Greens",
            "minimum": 0.0,
            "cbar_reverse": False,
            "color_threshold": {
                "minimum": 1e1,
                "maximum": 1e6,
            },
            "size": [25, 150],
        },
        "max_Sv": {
            "name": "Max $\\mathregular{S_V}$",
            "units": "dB re 1 $\\mathregular{m^-1}$",
            "colormap": "Blues",
            "minimum": -999,
            "cbar_reverse": False,
            "color_threshold": {"minimum": -80.0, "maximum": -36.0},
            "size": [5, 100],
        },
        # "mean_Sv": {
        #     "name": "$Mean \\mathregular{S_V}$",
        #     "units": "dB re. 1 $\\mathregular{m^-1}$",
        #     "colormap": "viridis",
        #     "minimum": -999,
        #     "cbar_reverse": True,
        #     "color_threshold": {
        #         "minimum": -80.0,
        #         "maximum": -36.0
        #     }
        # },
    }

    # List of variables to plot
    variables = list(VARIABLE_MAP.keys())

    # Go completed variables
    intact_variables = [var for var in variables if not survey_gdf[var].isnull().all()]

    def scale_sizes(values, min_value, max_value, min_size=25, max_size=250):

        # Censor values if needed
        sizes = values.copy()
        sizes.loc[sizes < min_value] = min_value
        sizes.loc[sizes > max_value] = max_value

        return ((sizes - min_value) / (max_value - min_value)) * (max_size - min_size) + min_size

    # Define colors for ship_ids (you can customize these colors as needed)
    ship_id_colors = {
        ship_id: plt.cm.tab10(i)  # Use a colormap for distinct colors; adjust as needed
        for i, ship_id in enumerate(survey_gdf["ship_id"].unique())
    }

    # Create a figure and a 2xn grid of subplots
    if len(intact_variables) == 4:
        fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    elif len(intact_variables) == 3:
        fig, axes = plt.subplots(1, 3, figsize=(10, 10))
    elif len(intact_variables) == 2:
        fig, axes = plt.subplots(1, 1, figsize=(10, 10))
    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9, wspace=0.0, hspace=0.0)

    # Iterate through and plot all subplots
    for ax, var in zip(axes.flat, intact_variables):
        # # ---- Get the colormap
        # colormap = plt.colormaps.get_cmap(VARIABLE_MAP[var]["colormap"]).resampled(256)
        # # ---- Invert
        # if VARIABLE_MAP[var]["cbar_reverse"]:
        #     newcolors = colormap(np.linspace(0, 1, 256))[::-1]
        # else:
        #     newcolors = colormap
        # # ---- Create the new custom colormap
        # custom_cmap = ListedColormap(newcolors)
        custom_cmap = VARIABLE_MAP[var]["colormap"]
        # ---- Plot cruisetrack
        # survey_gdf.plot(ax=ax, color="dimgray", linewidth=0.25, linestyle="-")
        # ax.plot(survey_gdf.geometry.x, survey_gdf.geometry.y, color="dimgray",
        #         linewidth=0.25, linestyle="-")
        handles = []  # List to store legend handles
        for ship_id, group in survey_gdf.groupby("ship_id"):
            # Sort the group by latitude or longitude
            # group = group.sort_values(by=["latitude", "longitude"])
            # color = ship_id_colors.get(ship_id, "gray")
            (line_handle,) = ax.plot(
                group.geometry.x,
                group.geometry.y,
                color="gray",
                linewidth=0.25,
                linestyle="-",
                label=ship_id,
                zorder=2,
            )
            handles.append(line_handle)  # Add handle to legend
            # ax.plot(group.geometry.x, group.geometry.y, label=ship_id, linewidth=0.25,
            #         linestyle="-", zorder=1)
        # ---- Drop "empty" values
        sub_gdf = survey_gdf[survey_gdf[var] > VARIABLE_MAP[var]["minimum"]]
        # ---- Assign color range
        if "color_threshold" in VARIABLE_MAP[var].keys():
            min_value = VARIABLE_MAP[var]["color_threshold"]["minimum"]
            max_value = VARIABLE_MAP[var]["color_threshold"]["maximum"]
        else:
            min_value = sub_gdf[var].min()
            max_value = sub_gdf[var].max()
        # ---- Normalize colorscale
        norm = plt.Normalize(vmin=min_value, vmax=max_value)
        # ---- Plot the points with color fills based on the variable (non-zero)
        ax.scatter(
            [geom.x for geom in sub_gdf.geometry],
            [geom.y for geom in sub_gdf.geometry],
            c=sub_gdf[var],
            # s=20,
            s=scale_sizes(
                values=sub_gdf[var],
                min_value=min_value,
                max_value=max_value,
                min_size=VARIABLE_MAP[var]["size"][0],
                max_size=VARIABLE_MAP[var]["size"][1],
            ),
            cmap=custom_cmap,
            norm=norm,
            zorder=1,
            alpha=0.6,
            lw=0,
            # edgecolor="black",
            # linewidths=0.1
        )
        # ---- Add coastline data layer
        coast_gdf.plot(ax=ax, linewidth=1.2, color="gray", edgecolor="black")
        # ---- Set axis limits
        ax.set_xlim(axis_limits[0] * 1.005, axis_limits[2] * 0.995)
        ax.set_ylim(axis_limits[1] * 0.98, axis_limits[3] * 1.005)
        # ---- Trim down the margins
        ax.margins(0, 0)
        # ---- Set adjustable aspect ratio
        # ax.set_aspect('equal', adjustable='box')
        # ---- Set the title and labels
        var_info = VARIABLE_MAP[var]
        ax.set_title(f"{var_info['name']}")
        # ---- Set axis labels
        ax.set_xlabel("Longitude (\u00B0E)")
        ax.set_ylabel("Latitude (\u00B0N)")
        # ---- Add colorbar
        sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
        sm._A = []  # fake up the array of the scalar mappable
        cbar = fig.colorbar(sm, ax=ax, shrink=0.5, fraction=0.075, pad=0.1)
        cbar.set_label(f"{var_info['units']}")
        # ---- Add scalebar
        scalebar_length = 100  # Length of scale bar in km
        scalebar_length_in_degrees = scalebar_length / 111  # Assuming 1 degree = 111 km
        # ---- Transform scale bar coordinates to axis units
        # scalebar_x = axis_limits[0]*1.005 + (axis_limits[2]*1.01 - axis_limits[0]*1.005) * 0.1
        # scalebar_y = axis_limits[1]*0.98 + (axis_limits[3]*1.005 - axis_limits[1]*0.98) * 0.1
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        x_scale = (x1 - x0) * 0.1
        y_scale = (y1 - y0) * 0.1
        # scalebar_y_offset = (axis_limits[3]*1.005 - axis_limits[1]*0.98) * 0.05
        # ---- Plot scalebar
        # ax.plot([scalebar_x, scalebar_x + scalebar_length / 100],
        #         [scalebar_y, scalebar_y], color='black', lw=2)
        ax.plot(
            [x0 + x_scale, x0 + x_scale + scalebar_length_in_degrees],
            [y0 + y_scale, y0 + y_scale],
            color="black",
            lw=2,
        )
        # ---- Add scale text
        ax.text(
            x0 + x_scale + scalebar_length_in_degrees / 2,
            y0 + y_scale - (y1 - y0) * 0.025,
            f"{scalebar_length} km",
            ha="center",
            va="top",
            color="black",
        )
        # ax.legend(handles=handles, title='Ship ID')

        # ax.text(scalebar_x + (scalebar_length / 200),
        #         scalebar_y - scalebar_y_offset,
        #         f'{scalebar_length} km', ha='center', va='bottom', color='black')

    # Adjust layout
    plt.tight_layout()

    # Show the plot
    # plt.show()
    return fig


def plot_livesurvey_distributions(
    weight_table: pd.DataFrame,
    stratum_table: pd.DataFrame,
    specimen_table: pd.DataFrame,
    length_table: pd.DataFrame,
    biology_db: Optional[Path] = None,
):

    # If calling from SQL database
    if biology_db is not None:
        weight_table = SQL(biology_db, "select", table_name="length_weight_df")
        stratum_table = SQL(biology_db, "select", table_name="strata_summary_df")
        specimen_table = SQL(biology_db, "select", table_name="specimen_data_df")
        length_table = SQL(biology_db, "select", table_name="length_df")
    elif not all(
        [
            isinstance(df, pd.DataFrame)
            for df in [weight_table, stratum_table, specimen_table, length_table]
        ]
    ):
        raise TypeError("All tables must be a `pandas.DataFrame.")

    # Organize the weight table data
    # ---- Sum weights by stratum, sex, and length_bin
    aggregated_data = (
        weight_table.groupby(["stratum", "sex", "length_bin"])["weight"].sum().reset_index()
    )
    # ---- Create a column to indicate 'all' sexes
    aggregated_data_all = (
        aggregated_data.groupby(["stratum", "length_bin"])["weight"].sum().reset_index()
    )
    aggregated_data_all["sex"] = "all"
    # ---- Combine the male, female, and all data
    plot_weight_data = pd.concat([aggregated_data, aggregated_data_all], ignore_index=True)

    # Define the sexes
    sexes = plot_weight_data.sex.unique().tolist()

    # Organize the length table data
    bins = plot_weight_data.length_bin.unique() + 1
    full_bins = np.concatenate([[bins[0] - np.diff(bins).mean() / 2], bins])
    length_table["length_bin"] = pd.cut(
        length_table["length"], bins=full_bins, labels=bins - 1
    ).astype(float)
    # length_table_sex = (
    #     length_table.groupby(["stratum", "sex", "length_bin"])["length_count"].sum().reset_index()
    # )
    length_table_all = (
        length_table.groupby(["stratum", "length_bin"])["length_count"].sum().reset_index()
    )
    length_table_all["sex"] = "all"
    full_count = (
        specimen_table.meld(
            length_table_all, contrasts=["stratum", "sex", "species_id", "length_bin"]
        )
        .loc[lambda x: x.sex.isin(sexes)]
        .groupby(["stratum", "sex", "length_bin"])["length_count"]
        .sum()
        .reset_index()
    )
    full_count["total"] = full_count.groupby(["stratum", "sex"])["length_count"].transform("sum")
    full_count["number_proportion"] = full_count["length_count"] / full_count["total"]
    # ---- Combine into the full dataset for plotting
    plot_count_data = (
        plot_weight_data.merge(
            full_count.filter(["stratum", "sex", "length_bin", "number_proportion"]),
            on=["stratum", "sex", "length_bin"],
            how="left",
        )
    ).fillna(0.0)

    # Get a color map
    colors = plt.colormaps["tab10"]
    num_strata = len(stratum_table["stratum"].unique())
    num_sexes = len(sexes)
    # color_map = colors(num_strata)

    # Plot
    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(6, 8), sharex=True, sharey=True)
    plt.subplots_adjust(hspace=0.08, wspace=0.05, bottom=0.25)  # Adjust spacing between plots

    # Plot weights and counts
    for i, sex in enumerate(sexes):
        # Weight plot (left column)
        ax_weight = axes[i, 0]
        data_weight = plot_weight_data[plot_weight_data["sex"] == sex]
        for j, (stratum, group) in enumerate(data_weight.groupby("stratum")):
            # color = colors(i / num_strata) if num_strata > 1 else colors(0)
            color = colors(j / num_strata) if num_strata > 1 else colors(0)
            total = group["weight"].sum()
            group["proportions"] = group["weight"] / total if total > 0.0 else 0.0
            ms = 5 if group["proportions"].max() > 0.0 else 0.1
            # handle, = ax_weight.plot(group['length_bin'], group['proportions'], marker='o',
            #                          label=f'Stratum {stratum}', color=color, ms=ms)
            ax_weight.plot(
                group["length_bin"],
                group["proportions"],
                marker=".",
                label=f"Stratum {stratum}",
                color=color,
                lw=1,
                ms=ms,
            )
        if i == 0:
            ax_weight.set_title("Weight")
        if i < num_sexes - 1:  # No x-ticks for non-bottom plots
            ax_weight.set_xlabel("")
        if i == num_sexes // 2:
            ax_weight.set_ylabel("Within-stratum proportion [0, 1]")
        if i == num_sexes - 1:  # Bottom plot
            ax_weight.set_xlabel("Length bin (cm)")
        ax_weight.set_ylim(0.0, 0.8)
        # Add label in the top-left corner
        ax_weight.text(
            0.05,
            1.00 - 0.05 * (num_sexes - 1),
            sex.title(),
            transform=ax_weight.transAxes,
            fontsize=12,
            verticalalignment="top",
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"),
        )

        # Count plot (right column)
        ax_count = axes[i, 1]
        data_count = plot_count_data[plot_count_data["sex"] == sex]
        for j, (stratum, group) in enumerate(data_count.groupby("stratum")):
            color = colors(j / num_strata) if num_strata > 1 else colors(0)
            ms = 5 if group["number_proportion"].max() > 0.0 else 0.1
            ax_count.plot(
                group["length_bin"],
                group["number_proportion"],
                marker=".",
                label=f"Stratum {stratum}",
                color=color,
                lw=1,
                ms=ms,
            )
        if i == 0:
            ax_count.set_title("Number")
        if i < num_sexes - 1:  # No x-ticks for non-bottom plots
            ax_count.set_xlabel("")
        if i == num_sexes - 1:  # Bottom plot
            ax_count.set_xlabel("Length bin (cm)")
        ax_count.set_ylim(0.0, 0.8)
        # Add label in the top-left corner
        ax_count.text(
            0.05,
            1.00 - 0.05 * (num_sexes - 1),
            sex.title(),
            transform=ax_count.transAxes,
            fontsize=12,
            verticalalignment="top",
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"),
        )
    # Create a new axes for the legend
    legend_ax = fig.add_axes(
        [0.15, 0.05, 0.7, 0.1]
    )  # Position the legend axes (left, bottom, width, height)
    legend_ax.axis("off")  # Hide the new axes

    # Create a shared legend in the bottom-most subplot
    handles, labels = axes[
        2, 1
    ].get_legend_handles_labels()  # Get handles and labels from the bottom-left plot
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.2),
        ncol=num_strata // 2 + 1,
        fontsize="small",
        title="INPFC stratum",
    )

    # plt.show()
    return fig
