"""
Tests unitaires pour la combinaison pondérée (GWPI) et la classification.
"""

import numpy as np
import pytest
from src.hydromap.overlay import calculate_class_areas, classify_potential, compute_gwpi


def test_compute_gwpi_weights_and_mask():
    """Vérifie le calcul correct de GWPI et l'application du masque."""
    h, w = 10, 10
    layers = {
        "geology": np.full((h, w), 0.8),
        "rainfall": np.full((h, w), 0.6),
        "slope": np.full((h, w), 0.4),
        "tpi": np.full((h, w), 0.2),
    }
    weights = {"geology": 0.4, "rainfall": 0.3, "slope": 0.2, "tpi": 0.1}

    # Calcul attendu : 0.4*0.8 + 0.3*0.6 + 0.2*0.4 + 0.1*0.2 = 0.32 + 0.18 + 0.08 + 0.02 = 0.60
    gwpi = compute_gwpi(layers, weights)
    assert np.allclose(gwpi, 0.60, atol=1e-4)

    # Vérification du masque
    mask = np.ones((h, w), dtype=bool)
    mask[0, 0] = False
    gwpi_masked = compute_gwpi(layers, weights, mask=mask)
    assert np.isnan(gwpi_masked[0, 0])
    assert not np.isnan(gwpi_masked[1, 1])


def test_gwpi_invalid_weights_sum():
    """Vérifie qu'une somme de poids différente de 1.0 lève une exception."""
    layers = {"c1": np.zeros((5, 5))}
    weights = {"c1": 0.5}  # Somme = 0.5 != 1.0

    with pytest.raises(ValueError):
        compute_gwpi(layers, weights)


def test_classify_potential_quantiles():
    """Vérifie la discrétisation en 4 classes."""
    # Grille linéaire continue de 0 à 1
    grid = np.linspace(0.0, 1.0, 100).reshape(10, 10)
    classes, thresholds = classify_potential(grid, method="quantiles", n_classes=4)

    assert len(thresholds) == 3
    # Les classes doivent aller de 1 à 4
    unique_classes = set(classes.flatten())
    assert unique_classes == {1.0, 2.0, 3.0, 4.0}


def test_calculate_class_areas():
    """Vérifie le calcul des superficies en km² et pourcentages."""
    grid = np.array([[1, 2], [3, 4]], dtype=float)
    # 4 pixels de 1km (1000m) -> 1 km² chacun
    areas = calculate_class_areas(grid, resolution_m=1000.0)

    assert len(areas) == 4
    for c in range(1, 5):
        assert areas[c]["area_km2"] == 1.0
        assert areas[c]["percentage"] == 25.0
