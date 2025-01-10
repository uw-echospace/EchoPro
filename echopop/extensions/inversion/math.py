"""
Mathematical and numerical utility functions.
"""

from typing import Any, Dict, Literal

import numpy as np
from numpy.typing import ArrayLike
from scipy.special import spherical_jn, spherical_yn


def spherical_hn(n, z, derivative=False) -> ArrayLike:
    """
    Spherical Bessel function of the third kind (Hankel function) or its derivative

    Defined as [1]_,

    .. math:: h_n^{(1)}(z)=j_n(z)+in_n(z),

    where :math:`h_n^{(1)}` is the spherical Bessel function of the third kind (or Hankel function
    of the first kind), :math:`j_n` is the spherical Bessel function of the first kind, :math:`n_n`
    is the spherical Bessel function of the second kind (or Neumann function), :math:`n` is the
    order of the function (:math:`n>=0`), :math:`z` is the Bessel function argument value, and
    :math:`i` is an imaginary number.

    Parameters
    ----------
    n: int
        Order of the Bessel function (n >= 0)
    z: Union[float, np.complex]
        Argument of the Bessel function
    derivative: Optional[bool]
        When True, the derivative is computed

    Notes
    -----
    The derivative is computed using the relations [2]_,

    .. math::
        \frac{n}{z} h^{(1)}_n - h^{(1)}_{n+1}(z)

    References
    ----------
    .. [1] https://dlmf.nist.gov/10.47#E5
    .. [2] https://dlmf.nist.gov/10.51#E2

    """
    # == lib/sphhn.m

    # Define internal function
    def _spherical_hn(n, z):
        return spherical_jn(n, z) + 1j * spherical_yn(n, z)

    # Computing derivative
    if derivative:
        return (n / z) * _spherical_hn(n, z) - _spherical_hn(n + 1, z)
    else:
        return _spherical_hn(n, z)


def length_average(
    length: ArrayLike[float],
    form_function: ArrayLike[complex],
    distribution_kwargs: Dict[str, float],
    distribution: Literal["gaussian", "uniform"] = "gaussian",
) -> ArrayLike:
    """
    Compute the length-averaged linear backscattering cross-section (:math:`\sigma_{bs}(L)`)
    """
    # == Scat_models/length_ave.m

    # PHASE 1) EXTRACT RELEVANT PARAMETERS (e.g. ka)
    # PHASE 2) GENERATE PDF BASED ON SELECTED DISTRIBUTION
    if distribution == "gaussian":
        pass
    elif distribution == "uniform":
        pass
    else:
        raise ValueError("Invalid distribution type. Choose 'gaussian' or 'uniform'.")
    # PHASE 3) SQUARE SIGMA_BS
    # PHASE 4) COMPUTE SIGMA_BS OVER CONFIGURED PDF BINS AT EACH DEFINED FREQUENCY

    # RETURNS: sqrt(sum(sigma_bs))
    pass


def orientation_average(
    angle: ArrayLike[float],
    form_function: ArrayLike[complex],
    distribution_kwargs: Dict[str, float],
    distribution: Literal["gaussian", "uniform"] = "gaussian",
) -> ArrayLike:
    """
    Compute the orientation-averaged linear backscattering cross-section :math:`\sigma_{bs}(\theta)`
    """
    # == Scat_models/orient_ave.m

    # PHASE 1) EXTRACT RELEVANT PARAMETERS (e.g. ka)
    # PHASE 2) GENERATE PDF BASED ON SELECTED DISTRIBUTION
    if distribution == "gaussian":
        pass
    elif distribution == "uniform":
        pass
    else:
        raise ValueError("Invalid distribution type. Choose 'gaussian' or 'uniform'.")
    # PHASE 3) SQUARE SIGMA_BS
    # PHASE 4) COMPUTE SIGMA_BS OVER CONFIGURED PDF BINS AT EACH DEFINED FREQUENCY

    # RETURNS: sqrt(sum(sigma_bs))
    pass


def fit_rayleigh_pdf(
    measured: ArrayLike[float],
    density: ArrayLike[float],
    mean: float,
    standard_deviation: float,
    lower_bounds: float,
    upper_bounds: float,
    arg_distribution: Literal["exponential", "gaussian"] = "gaussian",
):
    """
    Fit a single-parameter Rayleigh probability density function to the measured data
    """
    pass
