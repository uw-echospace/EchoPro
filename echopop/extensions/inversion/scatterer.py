"""
Scatterer class used for parameterizing and computing acoustic scattering models
"""

from typing import Any, Dict, Literal

import pandas as pd

from .scattering_models import pcdwba


class Scatterer:

    def __init__(
        self,
        parameters: Dict[str, Any],
        scattering_type: Literal[
            "elastic_shelled",
            "fluid_like",
            "resonant",
        ] = "fluid_like",
        shape: Literal[
            "arbitrary", "cylinder", "oblate_spheroid", "prolate_spheroid", "sphere", "umbrella"
        ] = "arbitrary",
    ):

        # Initialize attributes
        # ---- Model parameters
        self.parameters = parameters
        # ---- Scattering-type
        self.scattering_type = scattering_type
        # ---- Shape-type
        self.shape = shape

        # Build position matrix
        self.position_vector = construct_position_vector(self.shape, self.parameters)

    def compute_ts(
        self, scattering_parameters: Dict[str, Any], position_vector: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute theoretical target strength (TS)
        """

        # PHASE 1) EXTRACT PARAMETERS
        # PHASE 2) MAP RELEVANT SCATTERING CALLABLE FUNCTION (e.g. `pcdwba`)
        # PHASE 3) COMPUTE TS

        # RETURNS: DataFrame with TS values mapped to specific parameter values
        pass

    def predict_Sv(self, scattering_parameters: Dict[str, Any]) -> pd.DataFrame:

        # PHASE 1) EXTRACT PARAMETERS
        # PHASE 2) AVERAGE SIGMA_BS (LIKE IN EchoPro_matlab_krill_inversion::DWBAscat_simple1.m)

        # RETURNS: DataFrame (or np.ndarray?) of predicted Sv values
        pass


####################################################################################################
# UTILITY FUNCTIONS
####################################################################################################


def construct_position_vector(
    shape: Literal[
        "arbitrary", "cylinder", "oblate_spheroid", "prolate_spheroid", "sphere", "umbrella"
    ],
    scattering_parameters: Dict[str, Any],
) -> pd.DataFrame:
    """
    Construct position vector used for modeling
    """

    # PHASE 1) EXTRACT RELEVANT SHAPE PARAMETERS BASED ON SHAPE INPUT
    # PHASE 2) MAP RELEVANT SHAPE CALLABLE FUNCTION (e.g. `uniformly_bent_cylinder`)
    # PHASE 3) APPLY SHAPE FUNCTION
    # PHASE 4) ADD REMAINING COMPONENTS TO POSITION VECTOR IF NEEDED (e.g. heterogeneous material
    # properties)

    # RETURNS: DataFrame with position vector
    pass


def uniformly_bent_cylinder(scattering_parameters: Dict[str, Any]) -> pd.DataFrame:
    """
    Generates a uniformly bent cylinder
    """

    # PHASE 1) GET PARAMETERS
    # PHASE 2) GENERATE SHAPE

    # RETURNS: DataFrame with appropriate columns (dependent on shape)
    pass
