import numpy as np
import pandas as pd
import warnings
import sys
from matplotlib.colors import to_hex
from matplotlib import cm
import folium
import geopandas
from shapely.geometry import Polygon
from shapely.ops import unary_union
from scipy import interpolate


class KrigingMesh:
    """
    This class loads the mesh data, provides
    functions to manipulate the mesh, and
    provides functions to plot the mesh.

    Parameters
    ----------
    EPro : EchoPro object
        An initialized EchoPro object. Note that any change to
        self.EPro will also change this object.
    """

    def __init__(self, EPro = None):

        self.EPro = EPro

        # Default parameters for the folium map
        self.folium_map_kwargs = {
            'location': [44.61, -125.66],
            'zoom_start': 4,
            'tiles': 'CartoDB positron'
        }

        self.transect_transf_df = None
        self.transect_transf_D_x = None
        self.transect_transf_D_y = None
        self.mesh_transf_df = None
        self.__load_mesh()
        self.__load_smoothed_contour()

    def __load_mesh(self):
        """
        Loads the full mesh of the region being considered.
        Action is completed by reading in excel file determined
        by the user defined parameter ``'filename_grid_cell'``.

        Returns
        -------
        GeoPandas Dataframe representing the full mesh.
        """

        df = pd.read_excel(
            self.EPro.params['data_root_dir'] + self.EPro.params['filename_grid_cell'],
            sheet_name='krigedgrid2_5nm_forChu')  # TODO: make the sheet name an input

        # obtaining those columns that are required
        df = df[['Latitude of centroid', 'Longitude of centroid', 'Area (km^2)', 'Cell portion']].copy()

        # set data types of dataframe
        df = df.astype({'Latitude of centroid': float,
                        'Longitude of centroid': float,
                        'Area (km^2)': float,
                        'Cell portion': np.float64})

        df = geopandas.GeoDataFrame(df,
                                    geometry=geopandas.points_from_xy(
                                        df['Longitude of centroid'],
                                        df['Latitude of centroid']
                                    )
                                    )

        self.mesh_gdf = df

    def __load_smoothed_contour(self):
        """
        Loads the smoothed contour of the region being considered.
        Action is completed by reading in excel file determined
        by the user defined parameter ``'filename_smoothed_contour'``.

        Returns
        -------
        GeoPandas Dataframe representing the full mesh.
        """

        df = pd.read_excel(
            self.EPro.params['data_root_dir'] + self.EPro.params['filename_smoothed_contour'],
            sheet_name='Smoothing_EasyKrig')  # TODO: make the sheet name an input

        # obtaining those columns that are required
        df = df[['Latitude', 'Longitude']].copy()

        # set data types of dataframe
        df = df.astype({'Latitude': float,
                        'Longitude': float})

        df = geopandas.GeoDataFrame(df,
                                    geometry=geopandas.points_from_xy(df.Longitude, df.Latitude))

        self.smoothed_contour_gdf = df

    @staticmethod
    def get_coordinate_mean(gdf):
        """
        Creates a GeoPandas Dataframe representing
        the coordinate (latitude and longitude) mean
        of the provided Dataframe.

        Parameters
        ----------
        gdf : GeoPandas Dataframe
            All transect points with index transect and
            columns: Latitude, Longitude, and geometry.


        Returns
        -------
        A GeoPandas Dataframe containing the mean coordinate
        point (latitude, longitude) of each transect with
        index representing the transect and geometry column
        of shapely points.
        """

        # get the mean latitude and longitude based on the transects
        df_tran_mean = gdf[["Latitude", "Longitude"]].groupby(level=0).mean()

        return geopandas.GeoDataFrame(df_tran_mean,
                                      geometry=geopandas.points_from_xy(df_tran_mean.Longitude,
                                                                        df_tran_mean.Latitude))

    def get_polygon_of_transects(self, gdf, n_close, nm_to_buffer=1.25):
        """
        This function constructs a polygon that contains
        all transects.

        Parameters
        ----------
        gdf : GeoPandas Dataframe
            All transect points with index transect and
            columns: Latitude, Longitude, and geometry
        n_close : int
            The number of closest transects to include in the Polygon.
            This value includes the transect under consideration. Thus,
            n_close should be greater than or equal to 2.
        nm_to_buffer : float
            The number of nautical miles to buffer the constructed Polygon

        Returns
        -------
        Polygon that contains all transect data

        Notes
        -----
        How it works: Using the mean latitude, longitude
        point of each transect, we find the ``n_close`` closest
        transects to each transect and construct a Polygon
        of these transects. Then, we compute the convex
        hull of this Polygon, which creates the smallest
        convex Polygon containing all the points in the object.
        Lastly, we take the unary union of all constructed
        convex Polygons.

        The connectivity of this polygon
        is determined by ``n_close``.
        """

        gdf_tran_mean = self.get_coordinate_mean(gdf)

        transect_polygons = []
        for transect in gdf_tran_mean.index:
            closest_trans = gdf_tran_mean.geometry.distance(
                gdf_tran_mean.loc[transect,
                                  'geometry']).nsmallest(n_close)

            full_pol = Polygon(list(gdf.loc[closest_trans.index, "geometry"]))
            transect_polygons.append(full_pol.convex_hull)

        pol = unary_union(transect_polygons)

        # 1 degree of latitude equals 60nm
        # buffer Polygon by a number of nm
        buf_val = (1.0 / 60.0) * nm_to_buffer

        return pol.buffer(buf_val)

    def reduce_grid_points(self, transect_polygon):
        """
        Reduces the full mesh points provided to the ``KrigingMesh``
        class by selecting those points that are within the
        transect polygon.

        Parameters
        ----------
        transect_polygon : Polygon
            A Polygon that contains all transect data.

        Returns
        -------
        GeoPandas Dataframe representing the reduced
        mesh points
        """

        # get bool mask of points that are within the polygon
        in_poly = self.mesh_gdf['geometry'].within(transect_polygon)

        # select gdf rows based on bool mask
        return self.mesh_gdf.loc[in_poly]

    def apply_longitude_distance_transform(self, input_gdf, transform_type='transect'):
        # NOTE: mesh_df and transect_df are indeed geodataframes

        if transform_type == 'transect':
            # apply transformations to transect points
            transect_df = self.apply_longitude_transformation(input_gdf)
            D_x = transect_df.geometry.x.max() - transect_df.geometry.x.min()
            D_y = transect_df.geometry.y.max() - transect_df.geometry.y.min()
            x_transect, y_transect = self.apply_distance_transformation(transect_df, D_x, D_y)
            transect_df['x_transect'] = x_transect
            transect_df['y_transect'] = y_transect
            self.transect_transf_df = transect_df
            self.transect_transf_D_x = D_x
            self.transect_transf_D_y = D_y
        elif transform_type == 'mesh':
            # apply transformations to mesh points
            mesh_df = self.apply_longitude_transformation(input_gdf)
            x_mesh, y_mesh = self.apply_distance_transformation(
                mesh_df,
                self.transect_transf_D_x,
                self.transect_transf_D_y
            )
            mesh_df['x_mesh'] = x_mesh
            mesh_df['y_mesh'] = y_mesh

            self.mesh_transf_df = mesh_df

    def apply_distance_transformation(
            self,
            gdf,
            D_x,
            D_y,
            x_offset=-124.78338,
            y_offset=45.0
    ):
        """
        Transforms the input coordinates from degrees
        to distance i.e. puts them into a distance
        coordinate system.

        Parameters
        ----------
        gdf : Geopandas Dataframe or Pandas Dataframe
            Dataframe with columns specifying Latitude, Longitude,
            and geometry.
         D_x, D_y # TODO: fill in these detail, if necessary
        gdf_lon_name : str
            Name of the longitude column in gdf
        gdf_lat_name : str
            Name of the latitude column in gdf
        x_offset : float
            An arbitrary scalar, or a reference longitude
            (e.g., the mean longitude of the 200m isobath)
        y_offset : float
            An arbitrary scalar, or a reference latitude
            (e.g., the mean latitude of the 200m isobath)

        Returns
        -------
        x : Numpy array
            1D array representing the x coordinate of the distance
            coordinate system
        y : Numpy array
            1D array representing the y coordinate of the distance
            coordinate system

        Notes
        -----
        Extreme caution should be used here. This transformation
        was specifically designed for a NWFSC application!
        """

        # constant that converts degrees to radians
        DEG2RAD = np.pi / 180.0

        # initial coordinates without distance transformation
        x = gdf.geometry.x
        y = gdf.geometry.y

        # get normalization constants
        # D_x = x.max() - x.min()
        # D_y = y.max() - y.min()

        # transform the coordinates so they are in terms of distance
        x = np.cos(DEG2RAD * y) * (x - x_offset) / D_x
        y = (y - y_offset) / D_y

        return x.values.flatten(), y.values.flatten()

    def apply_longitude_transformation(self, gdf, lon_ref=-124.78338):
        """
        This function applies a transformation to the
        longitude column of the provided Dataframe so that
        the anisotropic signature of the animal biomass
        distribution can be approximately characterized by two
        perpendicular (principal) correlation scales: one is
        along the isobaths and the other is across the isobaths.

        Parameters
        ----------
        gdf : Geopandas Dataframe or Pandas Dataframe
            Dataframe with columns specifying Latitude, Longitude,
            and geometry.
        gdf_lon_name : str
            Name of the longitude column in gdf
        gdf_lat_name : str
            Name of the latitude column in gdf
        lon_ref : float
            An arbitrary scalar, or a reference longitude
            (e.g., the mean longitude of the 200m isobath)

        Returns
        -------
        A copy of ``gdf`` with the Longitude column transformed
        according to the interpolated (Latitude, Longitude) values
        pulled from the file specified by the parameter
        ``filename_smoothed_contour``.

        Notes
        -----
        Extreme caution should be used here. This transformation
        was specifically designed for a NWFSC application!
        """

        f = interpolate.interp1d(self.smoothed_contour_gdf['Latitude'],
                                 self.smoothed_contour_gdf['Longitude'],
                                 kind='linear', bounds_error=False)

        # TODO: do we need to drop NaNs after interpolating?
        #  Investigate this further.

        transformed_gdf = gdf.copy()
        transformed_gdf['longitude_transformed'] = gdf.geometry.x - f(gdf.geometry.y) + lon_ref
        transformed_gdf['geometry'] = geopandas.points_from_xy(
            transformed_gdf['longitude_transformed'],
            gdf.geometry.y
        )

        return transformed_gdf

    def get_folium_map(self, map_kwargs=None):
        """
        Grabs the folium map.

        Parameters
        ----------
        map_kwargs : dict
            Dictionary of kwargs for the folium.Map function.

        Returns
        -------
        A folium map object with provided specifications.

        Notes
        -----
        If ``map_kwargs`` is empty, then the default dictionary
        ``map_kwargs={'location': [44.61, -125.66], 'zoom_start': 4,
        'tiles': 'CartoDB positron'}`` will be used.
        """

        if map_kwargs is None:
            map_kwargs = self.folium_map_kwargs

        fmap = folium.Map(**map_kwargs)

        return fmap

    def plot_points(self, df, 
                    fmap=None, cmap_column=None,
                    color='hex', marker_kwargs={}):
        """
        Allows for a simple way to plot and
        visualize mesh points on a folium map.

        Parameters
        ----------
        fmap
            Folium map to plot the points on
        df : Pandas Dataframe
            Contains  Longitude and Latitude columns named ``lon_name``
            and ``lat_name``, respectively
        lat_name : str
            The name of the Latitude column in df
        lon_name : str
            The name of the Longitude column in df
        color : str
            The color of the markers representing the points. If
            color='hex', then a matplotlib color map will be created.
        cmap_column : str
            Column of geo_df that the colormap should correspond
            to. This is only used if color='hex'.
        marker_kwargs : dict
            Dictionary of kwargs that should be provided to
            folium.CircleMarker
        # TODO: make kwargs for folium.Map

        Returns
        -------
        folium.Map

        Notes
        -----
        If ``fmap`` is not provided, then a default folium map
        will be created using the class function ``get_folium_map``.
        """

        if fmap is None:
            fmap = self.get_folium_map()

        if color == 'hex':
            df = df.reset_index()  # TODO: this was specifically done for final_biomass_table, should we keep this?
            uniq_vals = df[cmap_column].unique()
            cmap = cm.get_cmap('viridis', len(uniq_vals))
            hex_color_options = {rgb[0]: to_hex(rgb[1])
                                 for rgb in zip(uniq_vals, cmap(uniq_vals))}

        for index, row in df.iterrows():
            if color == 'hex':
                color_val = hex_color_options[row[cmap_column]]
            else:
                color_val = color

            # Place the markers with specific color
            fmap.add_child(
                folium.CircleMarker(location=(row.geometry.y, row.geometry.x),
                                    radius=1,
                                    color=color_val,
                                    **marker_kwargs)
            )

        return fmap
