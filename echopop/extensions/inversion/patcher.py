from pathlib import Path
from typing import Any, Dict, Union

import pandas as pd

from ...survey import Survey


def inversion_pipeline(
    acoustic_dataset_file: Union[str, Path],
    scattering_config_file: Union[str, Path],
    inversion_config_file: Union[str, Path],
) -> Dict[str, Any]:
    """
    Consolidated workflow for predicting volumetric backscatter using inverted scattering model
    parameters/inputs
    """

    # PHASE 1) READ IN DATASET FILE
    # PHASE 2) READ IN CONFIGURATION FILES
    # PHASE 3) PREPARE DATASET FOR INVERSION
    # PHASE 4) PREPARE CONFIGURATION SETTINGS FOR OPTIMIZATION CALCULATIONS
    # PHASE 5) PREPARE SCATTERING MODEL AND OBJECT
    # PHASE 6) INVERT SCATTERING MODEL
    # PHASE 7) CALCULATE POPULATION ESTIMATES

    # RETURNS: A dictionary with grouped DataFrame (or new columns appended to acoustic dataset
    # columns?) objects that incorporate the estimated population estimates from the inverted
    # scattering model. One key in this output would also comprise the simulation results from the
    # optimization for user scrutinization
    pass


def inversion_survey_patch(
    self: Survey,
    acoustic_dataset_file: Union[str, Path],
    scattering_config_file: Union[str, Path],
    inversion_config_file: Union[str, Path],
) -> None:
    """
    Patching method to add `inversion_pipeline` function as a method to the base `echopop::Survey`
    class
    """

    # NOTE: This would be patched using the import functions defined in
    # `extensions/survey_extentions.py`

    return inversion_pipeline(acoustic_dataset_file, scattering_config_file, inversion_config_file)
