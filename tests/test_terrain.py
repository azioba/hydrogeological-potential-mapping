"""
Tests unitaires pour l'analyse du relief et la gestion des effets de bord.
"""

import numpy as np
from src.hydromap.terrain import compute_slope, compute_tpi, robust_normalize


def test_robust_normalize():
    """Vérifie la normalisation entre 0 et 1 avec et sans inversion."""
    arr = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    norm = robust_normalize(arr, invert=False)

    assert np.isclose(norm[0], 0.0, atol=0.05)
    assert np.isclose(norm[-1], 1.0, atol=0.05)
    assert np.all(norm >= 0.0) and np.all(norm <= 1.0)

    norm_inv = robust_normalize(arr, invert=True)
    assert np.isclose(norm_inv[0], 1.0, atol=0.05)
    assert np.isclose(norm_inv[-1], 0.0, atol=0.05)


def test_slope_flat_surface():
    """Une surface parfaitement plane doit donner une pente de 0 degré."""
    dem = np.full((20, 20), 500.0, dtype=float)
    slope_deg, slope_norm = compute_slope(dem, resolution_m=1000.0)

    assert np.allclose(slope_deg, 0.0, atol=1e-4)


def test_slope_known_gradient():
    """Un dénivelé de 1000 m sur une distance de 1000 m donne arctan(1) = 45 degrés."""
    dem = np.zeros((10, 10), dtype=float)
    for col in range(10):
        dem[:, col] = col * 1000.0  # 1000m par pixel

    slope_deg, _ = compute_slope(dem, resolution_m=1000.0)
    # Loin des bords, la pente doit être de 45 degrés
    internal_slope = slope_deg[2:8, 2:8]
    assert np.allclose(internal_slope, 45.0, atol=1e-2)


def test_tpi_valleys_and_ridges():
    """Vérifie qu'un creux topographique produit bien un TPI négatif."""
    dem = np.full((15, 15), 300.0, dtype=float)
    # Creux au centre (dépression / vallée)
    dem[7, 7] = 250.0

    tpi_raw, _ = compute_tpi(dem, window_size=5)
    assert tpi_raw[7, 7] < 0.0  # TPI négatif en vallée
