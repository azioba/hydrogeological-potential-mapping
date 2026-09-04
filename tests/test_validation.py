"""
Tests unitaires pour les métriques de validation ROC-AUC et de sensibilité.
"""

import numpy as np
from src.hydromap.validation import compute_roc_auc, single_parameter_sensitivity


def test_roc_auc_perfect_classifier():
    """Un prédicteur parfait doit donner un score AUC de 1.0."""
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])

    fpr, tpr, auc = compute_roc_auc(y_true, y_scores)
    assert np.isclose(auc, 1.0, atol=1e-3)


def test_roc_auc_random_classifier():
    """Un prédicteur non discriminant donne un AUC proche de 0.5."""
    y_true = np.array([0, 1, 0, 1, 0, 1])
    y_scores = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

    fpr, tpr, auc = compute_roc_auc(y_true, y_scores)
    assert np.isclose(auc, 0.5, atol=0.1)


def test_single_parameter_sensitivity():
    """Vérifie le calcul des poids effectifs SPSA."""
    mask = np.ones((5, 5), dtype=bool)
    layers = {
        "l1": np.full((5, 5), 0.8),
        "l2": np.full((5, 5), 0.2),
    }
    weights = {"l1": 0.5, "l2": 0.5}

    spsa = single_parameter_sensitivity(layers, weights, mask)
    # L1 ayant une valeur plus forte (0.8 vs 0.2), son poids effectif spatial doit être supérieur
    assert spsa["l1"] > spsa["l2"]
    assert np.isclose(spsa["l1"] + spsa["l2"], 100.0, atol=1e-2)
