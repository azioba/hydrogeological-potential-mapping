"""
Tests unitaires pour le module AHP (Analytic Hierarchy Process).
"""

import numpy as np
import pytest
from src.hydromap.ahp import AHPModel, calculate_ahp_weights


def test_ahp_consistent_matrix():
    """Vérifie le calcul des poids et le CR sur une matrice hautement cohérente."""
    criteria = ["geology", "rainfall", "slope", "tpi"]
    matrix = [
        [1.0, 2.0, 3.0, 3.0],
        [0.5, 1.0, 2.0, 2.0],
        [1 / 3, 0.5, 1.0, 1.0],
        [1 / 3, 0.5, 1.0, 1.0],
    ]

    model = AHPModel(criteria, matrix)
    weights = model.get_weights()

    # 1. Somme des poids égale à 1.0
    assert np.isclose(sum(weights.values()), 1.0, atol=1e-4)

    # 2. Ordre de priorité attendu
    assert weights["geology"] > weights["rainfall"]
    assert weights["rainfall"] > weights["slope"]
    assert np.isclose(weights["slope"], weights["tpi"], atol=1e-3)

    # 3. Ratio de cohérence inférieur à 0.10
    assert model.cr < 0.10
    assert model.is_consistent is True


def test_ahp_inconsistent_matrix():
    """Vérifie qu'une matrice incohérente est bien détectée avec CR >= 0.10."""
    criteria = ["c1", "c2", "c3"]
    # Incohérence extrême : c1 >> c2, c2 >> c3, mais c3 >> c1
    matrix = [
        [1.0, 7.0, 1 / 7],
        [1 / 7, 1.0, 7.0],
        [7.0, 1 / 7, 1.0],
    ]

    model = AHPModel(criteria, matrix)
    assert model.cr >= 0.10
    assert model.is_consistent is False


def test_ahp_invalid_dimensions():
    """Vérifie qu'une matrice non carrée ou de mauvaise taille lève une exception."""
    criteria = ["c1", "c2"]
    matrix = [[1.0, 2.0, 3.0], [0.5, 1.0, 2.0]]

    with pytest.raises(ValueError):
        AHPModel(criteria, matrix)


def test_ahp_non_reciprocal():
    """Vérifie qu'une matrice non réciproque lève une exception."""
    criteria = ["c1", "c2"]
    matrix = [[1.0, 2.0], [0.8, 1.0]]  # 2.0 * 0.8 = 1.6 != 1.0

    with pytest.raises(ValueError):
        AHPModel(criteria, matrix)
