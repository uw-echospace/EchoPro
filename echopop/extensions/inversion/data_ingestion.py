from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd
from lmfit import Parameters
from pandera import DataFrameModel
from pydantic import BaseModel

####################################################################################################
# Validation / preparation
####################################################################################################


class inversion_configuration_validator(BaseModel):
    """
    Pydantic model for validating configuration parameters
    """

    # RETURNS: Dict[str, Any]
    pass


class dataset_validator(DataFrameModel):
    """
    Pandera model for validating dataset values
    """

    # RETURNS: pd.DataFrame
    pass


def prepare_scattering_model_inputs(scattering_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare scattering model parameter inputs
    """
    # == functions/set_para.m
    # == functions/inversion_para.m

    # PHASE 1) INGEST VALUES FROM CONFIGURATION FILE
    # PHASE 2) VALIDATE USING `inversion_configuration_validator`
    # PHASE 3) COMPUTE INTERMEDIATE VARIABLES (e.g. acoustic wavenumber, position matrix)
    # PHASE 4) PASS TO SCATTERER CLASS
    #          --> EXTERNAL TO THIS FUNCTION

    # RETURNS: Validated scattering model inputs
    pass


def prepare_dataset(dataset: pd.DataFrame) -> Dict[str, Any]:
    """
    Prepare dataset inputs
    """

    # PHASE 1) INGEST DATASET (*.xlsx)
    # PHASE 2) VALIDATE USING `dataset_validator`
    # PHASE 3) PARTITION DATASET BASED ON DIFFERENT ECHOMETRICS (e.g. mean Sv, median Sv)

    # RETURNS: Validated dataset DataFrame objects used for inversion
    pass


def prepare_inversion_settings(inversion_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare inversion configuration and parameterization
    """

    # PHASE 1) INGEST VALUES FROM CONFIGURATION FILE
    # PHASE 2) VALIDATE USING `inversion_configuration_validator`
    # PHASE 3) COMPUTE INTERMEDIATE VARIABLES (e.g. acoustic wavenumber, position matrix)

    # RETURNS: Validated inversion and optimization parameters
    pass


####################################################################################################
# Data ingestion
####################################################################################################


def yaml_configuration_reader(
    config_file: Union[str, Path]
) -> Dict[str, Union[float, int, Parameters, pd.DataFrame, str]]:
    """
    Read and validate the input parameterization YAML configuration
    """
    # == functions/load_para_data.m
    # == functions/load_geo_phy_para.m
    # == functions/get_simu_para.m

    # PHASE 1) READ CONFIGURATION FILE

    # RETURNS: Raw Dict[str, Any]
    pass


def dataset_reader(data_file: Union[str, Path]) -> pd.DataFrame:
    """
    Read aggregate acoustic backscatter measurements
    """
    # == functions/get_acoustic_data.m
    # == functions/load_MOCNESS_data.m
    # == functions/load_BIOMAPPER_data.m

    # PHASE 1) READ IN FILES

    # RETURNS: Raw pd.DataFrame (or Dict[str, Any]: see `prepare_dataset`)
    pass
