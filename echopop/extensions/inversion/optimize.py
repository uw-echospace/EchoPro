from typing import Any, Callable, Dict, Literal, Union

import numpy as np
from lmfit import Minimizer, Parameters
from numpy.typing import ArrayLike


def mae(
    prediction: ArrayLike[float],
    measurement: ArrayLike[float],
):
    """
    Mean absolute deviation (MAD) in logarithmic space (dB)
    """
    # == functions/cost_functionALL.m
    pass


def rmse(
    prediction: ArrayLike[float],
    measurement: ArrayLike[float],
):
    """
    Root mean square deviation (RMSE) in logarithmic space (dB)
    """
    # == functions/cost_functionALL.m
    pass


def normalize_optimization_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the optimization parameters
    """
    pass


def prepare_optimization(
    scattering_model_parameters: Dict[str, Any],
    optimization_settings: Dict[str, Any],
    cost_function: Callable = mad,
) -> Dict[str, Union[Minimizer, Parameters]]:
    """
    Prepare optimization settings
    """

    # PHASE 1) EXTRACT RELEVANT SCATTERING MODEL PARAMETERS
    # PHASE 2) CONVERT RELEVANT OPTIMIZATION PARAMETERS INTO ASSOCIATED `lmfit::Parameters`
    params = Parameters(**scattering_model_parameters)  # not actual code, just a placeholder
    # PHASE 3) WITH COST-FUNCTION, CREATE `lmfit::Minimizer` OBJECT
    # not actual code, just a placeholder
    minim = Minimizer(cost_function, params, **optimization_settings)
    # RETURNS: Dictionary with optimization parameters and minimizer
    return {"parameters": params, "minimizer": minim}


def optimize_scattering_model(
    predicted_Sv: ArrayLike[float],
    measured_Sv: ArrayLike[float],
    parameters: Parameters,
    cost_function: Minimizer,
    optimization_settings: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Optimize scattering model parameters
    """
    # == functions/SVpredictionALL.m
    # == KrillSvInversion_simu_data_2020_05_01.m

    # PHASE 1) RUN OPTIMIZATION
    # not actual code, just a placeholder
    parameters_optimized = cost_function.minimize(
        method="least_squares", **optimization_settings["config"]
    )
    # PHASE 2) CALCULATE MEAN ABSOLUTE DEVIATION
    mad_optimized = np.mean(np.abs(parameters_optimized.residual))
    # PHASE 3) EXTRACT THE BEST-FIT PARAMETERS
    best_fit_params = parameters_optimized.params.valuesdict()

    # RETURNS: Best-fit scattering model parameters
    return best_fit_params
