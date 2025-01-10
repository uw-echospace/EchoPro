from typing import Any, Dict

from numpy.typing import ArrayLike
from pydantic import BaseModel
from scipy.special import j1

from .math import spherical_hn


def pcdwba(
    scattering_parameters: Dict[str, Any],
) -> ArrayLike:
    """
    Phase-compensated distorted wave Born approximation (DWBA)

    Defined as [1]_,

    ..math::
        f(\phi)=(kaT)^2\frac{J_1(2kaT \cos{\theta})}{2kaT \cos{\theta}}
        e^{i\varepsilon ka(\vec{r}_{pos}/h)\cos{\beta}}

    where :math:`f` is the scattering amplitude, :math:`\phi` is the scatterer orientation angle
    relative to the incident sound wave, :math:`k` is the acoustic wavenumber, :math:`T` is the
    taper coefficient, :math:`a` is the radius at a specific point along the body, :math:`J_1` is
    the cylindrical Bessel function of the first kind, :math:`\theta` is the orientation angle
    relative to the incident sound wave at a specific point along the body, :math:`\varepsilon` is
    the length-to-radius ratio, :math:`\vec{r}_{pos}` is the positional vector, :math:`h` is the
    soundspeed contrast, and :math:`\beta` is the orientation of a specific point along the body.

    References
    ----------
    ..[1] Chu, D., and Ye, Z. (1999). A phase-compensated distorted wave Born approximation
    representation of the bistatic scattering by weakly scattering objects: Application to
    zooplankton

    """
    # == Scat_models/DWBAbscat1.m

    # PHASE 1) EXTRACT AND PREPARE PARAMETERS
    # PHASE 2) COMPUTE CALCULATIONS

    # RETURNS: np.ndarray of complex form function values
    pass


class validate_pcdwba(BaseModel):
    """
    Pydantic model for validating scattering model parameters specific to the PCDWBA
    """

    # RETURNS: Dict[str, Any]
    pass
