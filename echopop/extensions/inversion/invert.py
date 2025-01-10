from typing import Any, Callable, Dict, Literal, Union

import pandas as pd
from numpy.typing import ArrayLike


def normalize_scattering_model_parameters(
    scattering_model_parameters: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize the scattering model parameters
    """
    # == model_para_conversion.m
    pass


def Sv_prediction_error(
    measured_Sv: ArrayLike[float],
    predicted_Sv: ArrayLike[float],
):
    """
    Compute inverted volumetric backscattering strength ($S[v]$) prediction error
    """
    pass


def invert_population(
    measured_Sv: ArrayLike[float],
    predicted_Sv: ArrayLike[float],
    inverted_ts: ArrayLike[float],
    kwargs,  # other parameters
) -> ArrayLike[float]:  # or just a full DataFrame given the multiple estimates being calculated
    """
    Generate population estimates based on inverted TS model parameters
    """

    # PHASE 1) MEAN NUMBER DENSITY
    # PHASE 2) AREAL NUMBER DENSITY
    # PHASE 3) ABUNDANCE
    # PHASE 4) ANIMAL BODY DENSITY (g/cm^3)
    # PHASE 5) BIOMASS
    # PHASE 6) AREAL BIOMASS DENSITY
    # PHASE 7) COMPUTE TOTAL PREDICTION ERROR ("Qe")
    total_error = Sv_prediction_error(measured_Sv, predicted_Sv)

    # RETURNS: Array or DataFrame ot population estimates
    pass
