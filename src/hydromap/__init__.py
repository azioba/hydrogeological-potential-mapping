"""
HydroMap — Open-source toolkit for groundwater potential zone mapping.
Author: HAMIDOU BÂ Abdoul Aziz
License: MIT
"""

from .ahp import AHPModel, calculate_ahp_weights
from .terrain import compute_slope, compute_tpi, robust_normalize
from .overlay import compute_gwpi, classify_potential, calculate_class_areas
from .validation import (
    validate_model_roc,
    single_parameter_sensitivity,
    map_removal_sensitivity,
)

__version__ = "2.1.0"
__author__ = "HAMIDOU BÂ Abdoul Aziz"
__all__ = [
    "AHPModel",
    "calculate_ahp_weights",
    "compute_slope",
    "compute_tpi",
    "robust_normalize",
    "compute_gwpi",
    "classify_potential",
    "calculate_class_areas",
    "validate_model_roc",
    "single_parameter_sensitivity",
    "map_removal_sensitivity",
]
