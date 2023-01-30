from typing import List, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr


def _redistribute_age1_data(df: pd.DataFrame, abundance_data: bool):
    """
    Redistributes the first age bin data to the rest of the age bins
    by directly modifying the data in ``df``.

    Parameters
    ----------
    df: pd.DataFrame
        A DataFrame with rows corresponding to length bins and columns
        corresponding to age bins
    abundance_data: bool
        If True, ``df`` corresponds to abundance data (and will therefore
        have and ``Un-aged`` column that needs to be ignored), else does
        not correspond to abundance data
    """

    # get the sum of the values for each age bin
    age_bin_sum = df.sum(axis=0).values

    # fill in age 1 data with zero
    df.iloc[:, 0] = 0.0

    # select column indices that data will be redistributed to
    if abundance_data:
        column_inds = slice(1, -1)
    else:
        column_inds = slice(1, len(age_bin_sum))

    # redistribute age 1 data to the rest of the age bins
    df.iloc[:, column_inds] += (
        age_bin_sum[0] * df.iloc[:, column_inds] / age_bin_sum[column_inds].sum()
    )


def _compute_len_age_abundance(
    abundance_df: pd.DataFrame,
    ds: xr.Dataset,
    sex: str,
    kriging_vals: bool,
    exclude_age1: bool,
) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    Computes the abundance at each length and age bin for a specified
    gender using the input abundance DataFrame and parameter Dataset.

    Parameters
    ----------
    abundance_df: pd.DataFrame
        A DataFrame with index ``stratum_num`` and column with abundance
        values. If DataFrame corresponds to Kriging data then the column
        should be named ``abundance_adult``, else it should be named
        ``abundance``.
    ds: xr.Dataset
        A Dataset produced by the module ``parameters_dataset.py``, which
        contains all parameters necessary for computation
    sex: {'M', 'F'}
        A string specifying the gender for the abundance computation
    kriging_vals: bool
        If True, the abundance data was produced by Kriging, else
        it is Transect based
    exclude_age1: bool
        If True, exclude age 1 data, else do not (only applies to Kriging data)

    Returns
    -------
    Len_Age_Matrix_Acoust: xr.DataArray
        A DataArray representing the abundance at each length and age
        bin for the specified gender
    Len_Age_Matrix_Acoust_unaged: xr.DataArray
        A DatArray representing the abundance for the unaged data
        at each length bin
    """

    # obtain only those strata that are defined in abundance_df
    defined_stratum = abundance_df.index.unique().values

    # compute the total number of animals in both stations
    total_N = ds.num_M + ds.num_F + ds.station_1_N

    # compute the proportion of the sex using station 2 data
    Len_Age_sex_proportion = ds[f"num_{sex}"] / total_N

    # compute the proportion of the sex using station 1 data
    Len_sex_proportion = ds[f"station_1_N_{sex}"] / total_N

    # get the normalized distribution of data in station 2
    Len_Age_key_sex_norm = ds[f"len_age_dist_{sex}"] / ds[f"len_age_dist_{sex}"].sum(
        ["len_bin", "age_bin"]
    )

    # sum together all abundance values in each stratum
    if kriging_vals:
        abundance_sum_stratum = (
            abundance_df.groupby(level=0).sum()["abundance_adult"].to_xarray()
        )
    else:
        abundance_sum_stratum = (
            abundance_df.groupby(level=0).sum()["abundance"].to_xarray()
        )

    # get the abundance for the sex for each stratum (station 1)
    N_len = abundance_sum_stratum * Len_sex_proportion.sel(stratum_num=defined_stratum)

    # get the abundance for the sex for each stratum (station 2)
    N_len_age = abundance_sum_stratum * Len_Age_sex_proportion.sel(
        stratum_num=defined_stratum
    )

    # compute the abundance for the unaged data at each length bin
    Len_Age_Matrix_Acoust_unaged = (
        N_len
        * ds[f"len_dist_station1_normalized_{sex}"].sel(stratum_num=defined_stratum)
    ).sum("stratum_num")

    # get the abundance for the sex at each length and age bin
    Len_Age_Matrix_Acoust = (
        N_len_age * Len_Age_key_sex_norm.sel(stratum_num=defined_stratum)
    ).sum("stratum_num")

    return Len_Age_Matrix_Acoust, Len_Age_Matrix_Acoust_unaged


def _compute_transect_len_age_biomass(
    biomass_df: pd.DataFrame, ds: xr.Dataset
) -> xr.DataArray:
    """
    Computes the biomass at each length and age bin using the
    input biomass DataFrame and parameter Dataset, for the transect
    based data.

    Parameters
    ----------
    biomass_df: pd.DataFrame
        A DataFrame with index ``stratum_num`` and column with biomass
        values. If DataFrame corresponds to Kriging data then the column
        should be named ``biomass_adult``, else it should be named
        ``biomass``.
    ds: xr.Dataset
        A Dataset produced by the module ``parameters_dataset.py``, which
        contains all parameters necessary for computation

    Returns
    -------
    Len_Age_Matrix_biomass: xr.DataArray
        A DataArray representing the biomass at each length and age
        bin for provided biomass data
    """

    # obtain only those strata that are defined in biomass_df
    defined_stratum = biomass_df.index.unique().values

    # obtain the total biomass for each stratum
    biomass_sum_stratum = biomass_df.groupby(level=0).sum()["biomass"].to_xarray()

    # get the biomass for the sex at each length and age bin
    Len_Age_Matrix_biomass = (
        biomass_sum_stratum
        * ds.len_age_weight_dist_all_normalized.sel(stratum_num=defined_stratum)
    ).sum("stratum_num")

    # TODO: add this in when we implement the Kriging version
    # TODO: need to redistribute the data in a special way for biomass
    # redistribute the age 1 data if Kriging values are being used
    # if exclude_age1 and kriging_vals:
    #     self._redistribute_age1_data(Len_Age_Matrix_biomass)

    return Len_Age_Matrix_biomass


def _compute_kriging_len_age_biomass(
    biomass_df: pd.DataFrame, ds: xr.Dataset, sex: str
) -> xr.DataArray:
    """
    Computes the biomass at each length and age bin using the
    input biomass DataFrame and parameter Dataset, for the Kriging
    based data.

    Parameters
    ----------
    biomass_df: pd.DataFrame
        A DataFrame with index ``stratum_num`` and column with biomass
        values. If DataFrame corresponds to Kriging data then the column
        should be named ``biomass_adult``, else it should be named
        ``biomass``.
    ds: xr.Dataset
        A Dataset produced by the module ``parameters_dataset.py``, which
        contains all parameters necessary for computation

    Returns
    -------
    Len_Age_Matrix_biomass: xr.DataArray
        A DataArray representing the biomass at each length and age
        bin for provided biomass data
    """

    # TODO: document!

    # obtain only those strata that are defined in biomass_df
    defined_stratum = biomass_df["stratum_num"].values.unique()

    # create variables to improve readability
    biomass_density_adult_mean = biomass_df[["biomass_density_adult_mean"]]
    cell_area_nmi2 = biomass_df[["cell_area_nmi2"]]

    # calculate the biomass multiplied by the cell area and sum these values by stratum
    bio_times_area = biomass_df["stratum_num"].copy(deep=True).to_frame()
    bio_times_area["val"] = biomass_density_adult_mean.values * cell_area_nmi2.values
    sum_bio_area = (
        bio_times_area.set_index("stratum_num")
        .groupby(level=0)
        .sum()["val"]
        .to_xarray()
    )

    # calculate the aged biomass for males and females
    dist_weight_sum = (
        ds[f"len_age_weight_dist_{sex}_normalized"] * ds[f"len_age_weight_prop_{sex}"]
    ).sel(
        stratum_num=defined_stratum
    )  # .values

    biomass_aged = (dist_weight_sum * sum_bio_area).sum("stratum_num")

    weight_unaged = ds.weight_len_all_normalized * ds[f"unaged_{sex}_wgt_proportion"]

    # calculate the unaged biomass
    biomass_unaged = (weight_unaged * sum_bio_area).sum("stratum_num")

    # calculate the weight of the unaged for all genders
    weight_all_unaged = ds.weight_len_all_normalized * ds["unaged_proportion"]

    # calculate the unaged biomass for all genders
    biomass_all_unaged = (
        (weight_all_unaged * sum_bio_area).sum("stratum_num") * 1e-6
    ).values

    return biomass_aged, biomass_unaged, biomass_all_unaged


def get_len_age_abundance(
    gdf: gpd.GeoDataFrame, ds: xr.Dataset, kriging_vals: bool, exclude_age1: bool
) -> List[pd.DataFrame]:
    """
    Obtains and initiates the computation of the abundance at
    each length and age bin for male, female, and all
    gender data.

    Parameters
    ----------
    gdf: gpd.GeoDataFrame
        A GeoDataFrame with column ``stratum_num`` and a column with abundance
        values. If the GeoDataFrame corresponds to Kriging data then the column
        abundance column should be named ``abundance_adult``, else it should
        be named ``abundance``.
    ds: xr.Dataset
        A Dataset produced by the module ``parameters_dataset.py``, which
        contains all parameters necessary for computation
    kriging_vals: bool
        If True, the abundance data was produced by Kriging, else
        it is Transect based
    exclude_age1: bool
        If True, exclude age 1 data, else do not (only applies to Kriging data)

    Returns
    -------
    len_age_abundance_list: list of pd.DataFrame
        A list where each element is a DataFrame containing the abundance at
        each length and age bin for male, female, and all genders (in
        that order)
    """

    # obtain abundance data
    if kriging_vals:
        abundance_df = gdf[["abundance_adult", "stratum_num"]]
    else:
        abundance_df = gdf[["abundance", "stratum_num"]]

    # make stratum_num the index of the DataFrame
    abundance_df = abundance_df.reset_index(drop=True).set_index("stratum_num")

    # compute, format, and store the abundance data for male and females
    len_age_abundance_list = []
    for sex in ["M", "F"]:

        # compute the abundance at each length and age bin for a gender
        aged_da, unaged_da = _compute_len_age_abundance(
            abundance_df,
            ds,
            sex=sex,
            kriging_vals=kriging_vals,
            exclude_age1=exclude_age1,
        )

        # convert returned DataArray to a DataFrame
        aged_df = aged_da.to_pandas()

        # combine the aged and unaged abundance data
        final_df = pd.concat([aged_df, unaged_da.to_pandas()], axis=1)

        # create and assign column names
        final_df.columns = ["age_bin_" + str(column) for column in aged_df.columns] + [
            "Un-aged"
        ]

        # remove row header produced by xarray
        final_df.index.name = ""

        # create and assign index names
        final_df.index = ["len_bin_" + str(row_ind) for row_ind in final_df.index]

        # store DataFrame
        len_age_abundance_list.append(final_df)

    # create and add the length-age abundance df for both genders to list
    len_age_abundance_list += [len_age_abundance_list[0] + len_age_abundance_list[1]]

    # redistribute the age 1 data if Kriging values are being used
    if exclude_age1 and kriging_vals:
        for df in len_age_abundance_list:
            _redistribute_age1_data(df, abundance_data=True)

    return len_age_abundance_list


def get_transect_len_age_biomass(
    gdf_all: gpd.GeoDataFrame,
    gdf_male: gpd.GeoDataFrame,
    gdf_female: gpd.GeoDataFrame,
    ds: xr.Dataset,
) -> List[pd.DataFrame]:
    """
    Obtains and initiates the computation of the biomass at
    each length and age bin for male, female, and all
    gender data, for transect based data.

    Parameters
    ----------
    gdf_all: gpd.GeoDataFrame
        A GeoDataFrame with column ``stratum_num`` and column corresponding
        to the biomass produced by including all genders.
    gdf_male: gpd.GeoDataFrame
        A GeoDataFrame with column ``stratum_num`` and column corresponding
        to the biomass produced by including only males.
    gdf_female: gpd.GeoDataFrame
        A GeoDataFrame with column ``stratum_num`` and column corresponding
        to the biomass produced by including only females.
    ds: xr.Dataset
        A Dataset produced by the module ``parameters_dataset.py``, which
        contains all parameters necessary for computation

    Returns
    -------
    len_age_biomass_list: list of pd.DataFrame
        A list where each element is a DataFrame containing the biomass at
        each length and age bin for male, female, and all genders (in
        that order)
    """

    # compute, format, and store the biomass data for male, females, and all genders
    len_age_biomass_list = []
    for gdf in [gdf_male, gdf_female, gdf_all]:

        # obtain the biomass DataFrame
        biomass_df = gdf[["biomass", "stratum_num"]]

        # make stratum_num the index of the DataFrame
        biomass_df = biomass_df.reset_index(drop=True).set_index("stratum_num")

        # obtain the biomass at the length and age bins
        final_df = _compute_transect_len_age_biomass(biomass_df, ds).to_pandas()

        # remove column and row header produced by xarray
        final_df.columns.name = ""
        final_df.index.name = ""

        # create and assign column names
        final_df.columns = ["age_bin_" + str(column) for column in final_df.columns]

        # create and assign index names
        final_df.index = ["len_bin_" + str(row_ind) for row_ind in final_df.index]

        # store biomass data
        len_age_biomass_list.append(final_df)

    return len_age_biomass_list


def _redistribute_age1_kriged_biomass(len_age_biomass_list, biomass_unaged):

    # TODO: document!

    male_arr = len_age_biomass_list[0].to_numpy() * 1e-6
    female_arr = len_age_biomass_list[1].to_numpy() * 1e-6

    Uaged2aged_mat_M = np.zeros((male_arr.shape[0], male_arr.shape[1] - 1))
    Uaged2aged_mat_F = np.zeros((male_arr.shape[0], male_arr.shape[1] - 1))
    threshold = 1e-10
    eps = 2.22044604925031e-16

    for i in range(male_arr.shape[0]):

        if (sum(male_arr[i, :-1]) < threshold) and (
            sum(female_arr[i, :-1]) < threshold
        ):
            # neither male and nor female hake at ith length bin is found
            # for aged hake (bio-sample station 2)
            if male_arr[i, -1] < threshold:
                # no unaged hake found at bio-sample station 1
                Uaged2aged_mat_M[i, :] = 0.0
                Uaged2aged_mat_F[i, :] = 0.0
            else:

                # unaged hake found at bio-sample station 1
                sum_over_ageM = male_arr[:, :-1].sum(axis=1)
                ind_M = np.argwhere(sum_over_ageM > eps).flatten() + 1
                ind_sel_M = np.argmin(abs(ind_M - (i + 1))) + 1
                ind_sel_M = ind_sel_M + min(ind_M) - 1

                sum_over_ageF = female_arr[:, :-1].sum(axis=1)
                ind_F = np.argwhere(sum_over_ageF > eps).flatten() + 1
                ind_sel_F = np.argmin(abs(ind_F - (i + 1))) + 1
                ind_sel_F = ind_sel_F + min(ind_F) - 1

                if ind_sel_F < ind_sel_M:
                    # closet length bin has no aged female, using the smaller
                    # length bin aged female data
                    while sum(female_arr[ind_sel_F - 1, :-1]) == 0:
                        ind_sel_F = ind_sel_F - 1
                    Uaged2aged_mat_M[i, :] = (
                        male_arr[i, -1]
                        * female_arr[ind_sel_F - 1, :-1]
                        / sum(female_arr[ind_sel_F - 1, :-1])
                    )
                    Uaged2aged_mat_F[i, :] = (
                        female_arr[i, -1]
                        * female_arr[ind_sel_F - 1, :-1]
                        / sum(female_arr[ind_sel_F - 1, :-1])
                    )
                else:
                    # closet length bin has no aged male, using the smaller
                    # length bin aged male data
                    while sum(male_arr[ind_sel_M - 1, :-1]) == 0:
                        ind_sel_M = ind_sel_M - 1
                    Uaged2aged_mat_M[i, :] = (
                        male_arr[i, -1]
                        * male_arr[ind_sel_M - 1, :-1]
                        / sum(male_arr[ind_sel_M - 1, :-1])
                    )
                    Uaged2aged_mat_F[i, :] = (
                        female_arr[i, -1]
                        * male_arr[ind_sel_M - 1, :-1]
                        / sum(male_arr[ind_sel_M - 1, :-1])
                    )
        elif (sum(male_arr[i, :-1]) < threshold) and (male_arr[i, -1] > threshold):
            # no male hake at ith length bin for aged hake (bio-sample station 2)
            # but has for unaged hake (bio-sample station 1)
            Uaged2aged_mat_M[i, :] = (
                male_arr[i, -1] * female_arr[i, :-1] / sum(female_arr[i, :-1])
            )
            Uaged2aged_mat_F[i, :] = (
                female_arr[i, -1] * female_arr[i, :-1] / sum(female_arr[i, :-1])
            )
        elif (sum(female_arr[i, :-1]) < threshold) and (female_arr[i, -1] > threshold):
            # no female hake at ith length bin for aged hake (bio-sample station 2)
            # but has for unaged hake (bio-sample station 1)
            Uaged2aged_mat_M[i, :] = (
                male_arr[i, -1] * male_arr[i, :-1] / sum(male_arr[i, :-1])
            )
            Uaged2aged_mat_F[i, :] = (
                female_arr[i, -1] * male_arr[i, :-1] / sum(male_arr[i, :-1])
            )
        elif (
            (sum(male_arr[i, :-1]) > threshold)
            and (sum(female_arr[i, :-1]) > threshold)
            and (biomass_unaged[i] > threshold)
        ):
            # both male and female hake have samples at ith length bin for aged hake
            # (bio-sample station 2) and unaged hake (bio-sample station 1)
            Uaged2aged_mat_M[i, :] = (
                male_arr[i, -1] * male_arr[i, :-1] / sum(male_arr[i, :-1])
            )
            Uaged2aged_mat_F[i, :] = (
                female_arr[i, -1] * female_arr[i, :-1] / sum(female_arr[i, :-1])
            )

    len_age_biomass_list[0].iloc[:, :-1] += Uaged2aged_mat_M * 1e6
    len_age_biomass_list[1].iloc[:, :-1] += Uaged2aged_mat_F * 1e6


def get_kriging_len_age_biomass(
    gdf_all: gpd.GeoDataFrame,
    ds: xr.Dataset,
    exclude_age1: bool,
) -> List[pd.DataFrame]:
    """
    Obtains and initiates the computation of the biomass at
    each length and age bin for male, female, and all
    gender data, for Kriging based data.

    Parameters
    ----------
    gdf_all: gpd.GeoDataFrame
        A GeoDataFrame with column ``stratum_num`` and column corresponding
        to the biomass produced by including all genders. If GeoDataFrame
        corresponds to Kriging data then the column should be named
        ``biomass_adult``, else it should be named ``biomass``.
    ds: xr.Dataset
        A Dataset produced by the module ``parameters_dataset.py``, which
        contains all parameters necessary for computation
    exclude_age1: bool
        If True, exclude age 1 data, else do not (only applies to Kriging data)

    Returns
    -------
    len_age_biomass_list: list of pd.DataFrame
        A list where each element is a DataFrame containing the biomass at
        each length and age bin for male, female, and all genders (in
        that order)
    """

    # TODO: document

    # compute, format, and store the biomass data for male, females, and all genders
    len_age_biomass_list = []

    # obtain the biomass at the length and age bins
    for sex in ["M", "F"]:
        (
            biomass_aged,
            biomass_unaged,
            biomass_all_unaged,
        ) = _compute_kriging_len_age_biomass(gdf_all, ds, sex)

        aged_df = biomass_aged.to_pandas()

        final_df = pd.concat([aged_df, biomass_unaged.to_pandas()], axis=1)

        # remove column and row header produced by xarray
        final_df.columns.name = ""
        final_df.index.name = ""

        # create and assign column names
        final_df.columns = ["age_bin_" + str(column) for column in aged_df.columns] + [
            "Un-aged"
        ]

        # create and assign index names
        final_df.index = ["len_bin_" + str(row_ind) for row_ind in final_df.index]

        # store biomass data
        len_age_biomass_list.append(final_df)

    _redistribute_age1_kriged_biomass(len_age_biomass_list, biomass_unaged)

    len_age_biomass_list.append(len_age_biomass_list[0] + len_age_biomass_list[1])

    # redistribute the age 1 data if Kriging values are being used
    if exclude_age1:
        for df in len_age_biomass_list:
            _redistribute_age1_data(
                df, abundance_data=True
            )  # TODO: change name of abundance_data

    return len_age_biomass_list
