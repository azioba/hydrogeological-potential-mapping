"""
Module de validation hydrogéologique statistique et analyse de sensibilité.
Prend en charge la courbe ROC / AUC, la corrélation avec les forages réels (WPDx)
et les analyses de sensibilité SPSA (Single-Parameter) et MRSA (Map Removal).
"""

from typing import Dict, List, Optional, Tuple
import numpy as np


def extract_raster_at_points(
    raster: np.ndarray,
    transform,
    points_coords: List[Tuple[float, float]],
) -> np.ndarray:
    """
    Extrait les valeurs de pixels d'un raster aux coordonnées (X, Y).

    :param raster: Tableau 2D numpy (H, W)
    :param transform: Affine transform rasterio (ou tuple transform standard)
    :param points_coords: Liste de coordonnées (x, y) dans le CRS du raster
    :returns: Tableau 1D des valeurs extraites (float)
    """
    height, width = raster.shape
    values = []

    # Inversion affine pour convertir (x, y) en (col, row)
    inv_transform = ~transform

    for x, y in points_coords:
        col, row = inv_transform * (x, y)
        col_idx, row_idx = int(round(col)), int(round(row))

        if 0 <= row_idx < height and 0 <= col_idx < width:
            values.append(raster[row_idx, col_idx])
        else:
            values.append(np.nan)

    return np.array(values, dtype=float)


def compute_roc_auc(
    y_true: np.ndarray,
    y_scores: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Calcule manuellement et précisément la courbe ROC et le score AUC
    (sans dépendance obligatoire externe pour flexibilité).

    :param y_true: Étiquettes binaires (1 = forage productif, 0 = non-productif/sec)
    :param y_scores: Scores continus prédits (GWPI entre 0 et 1)
    :returns: Tuple (fpr, tpr, auc_score)
    """
    y_true = np.asarray(y_true, dtype=int)
    y_scores = np.asarray(y_scores, dtype=float)

    valid = ~np.isnan(y_scores) & ~np.isnan(y_true)
    y_true = y_true[valid]
    y_scores = y_scores[valid]

    if len(y_true) == 0 or len(np.unique(y_true)) < 2:
        return np.array([0.0, 1.0]), np.array([0.0, 1.0]), 0.5

    # Tri par score décroissant
    desc_order = np.argsort(-y_scores)
    y_scores_sorted = y_scores[desc_order]
    y_true_sorted = y_true[desc_order]

    num_pos = np.sum(y_true == 1)
    num_neg = np.sum(y_true == 0)

    if num_pos == 0 or num_neg == 0:
        return np.array([0.0, 1.0]), np.array([0.0, 1.0]), 0.5

    # Regrouper les seuils identiques (standard ROC / scikit-learn)
    distinct_value_indices = np.where(np.diff(y_scores_sorted))[0]
    threshold_idxs = np.r_[distinct_value_indices, y_true_sorted.size - 1]

    tpr = np.cumsum(y_true_sorted == 1)[threshold_idxs] / num_pos
    fpr = np.cumsum(y_true_sorted == 0)[threshold_idxs] / num_neg

    tpr = np.r_[0.0, tpr]
    fpr = np.r_[0.0, fpr]

    # Intégration trapézoïdale pour le score AUC (compatible NumPy 1.x et 2.x)
    trapz_func = getattr(np, "trapezoid", getattr(np, "trapz", None))
    if trapz_func is not None:
        auc_score = float(trapz_func(tpr, fpr))
    else:
        # Implémentation manuelle de secours
        auc_score = float(np.sum((fpr[1:] - fpr[:-1]) * (tpr[1:] + tpr[:-1]) / 2.0))

    return fpr, tpr, max(0.0, min(1.0, auc_score))


def validate_model_roc(
    gwpi_grid: np.ndarray,
    transform,
    points_coords: List[Tuple[float, float]],
    y_true_binary: List[int],
) -> Dict[str, object]:
    """
    Valide la capacité prédictive du modèle par rapport à des forages réels.

    :param gwpi_grid: Grille raster 2D GWPI
    :param transform: Rasterio transform
    :param points_coords: Coordonnées projetées des forages [(x, y), ...]
    :param y_true_binary: Liste d'indicateurs binaires (1 = productif, 0 = sec/faible débit)
    :returns: Dictionnaire avec AUC, FPR, TPR et synthèse d'évaluation
    """
    extracted_scores = extract_raster_at_points(gwpi_grid, transform, points_coords)
    fpr, tpr, auc = compute_roc_auc(np.array(y_true_binary), extracted_scores)

    evaluation = (
        "Excellent (AUC > 0.85)"
        if auc >= 0.85
        else "Bon (0.75 <= AUC < 0.85)"
        if auc >= 0.75
        else "Modéré (0.65 <= AUC < 0.75)"
        if auc >= 0.65
        else "Faible (AUC < 0.65)"
    )

    return {
        "auc": round(auc, 4),
        "fpr": fpr,
        "tpr": tpr,
        "n_points": len(points_coords),
        "n_valid_points": int(np.sum(~np.isnan(extracted_scores))),
        "quality_level": evaluation,
    }


def single_parameter_sensitivity(
    layers: Dict[str, np.ndarray],
    weights: Dict[str, float],
    mask: np.ndarray,
) -> Dict[str, float]:
    """
    Analyse de sensibilité à paramètre unique (Single-Parameter Sensitivity Analysis - SPSA).
    Calcule le poids effectif moyen (W_eff) de chaque critère sur le territoire :
        W_eff_i = (W_i × X_i / GWPI) × 100

    :param layers: Couches normalisées
    :param weights: Poids théoriques AHP
    :param mask: Masque de la zone d'étude
    :returns: Dictionnaire {critère: poids_effectif_moyen_%}
    """
    composite = np.zeros_like(mask, dtype=float)
    for k, w in weights.items():
        composite += w * layers[k].astype(float)

    valid = mask & ~np.isnan(composite) & (composite > 0)
    composite_valid = composite[valid]

    effective_weights: Dict[str, float] = {}

    for k, w in weights.items():
        layer_vals = layers[k][valid].astype(float)
        # Ratio effectif local
        local_effective = (w * layer_vals / composite_valid) * 100.0
        effective_weights[k] = float(np.nanmean(local_effective))

    # Normalisation pour sommer à 100%
    total = sum(effective_weights.values())
    if total > 0:
        effective_weights = {k: round((v / total) * 100.0, 2) for k, v in effective_weights.items()}

    return effective_weights


def map_removal_sensitivity(
    layers: Dict[str, np.ndarray],
    weights: Dict[str, float],
    mask: np.ndarray,
) -> Dict[str, float]:
    """
    Analyse de sensibilité par retrait de couche (Map Removal Sensitivity Analysis - MRSA).
    Mesure la variation du potentiel global lorsqu'une couche est omise :
        S_i = (|GWPI - GWPI_-i| / GWPI) × 100

    :returns: Dictionnaire {critère: indice_sensibilité_%}
    """
    composite = np.zeros_like(mask, dtype=float)
    for k, w in weights.items():
        composite += w * layers[k].astype(float)

    valid = mask & ~np.isnan(composite) & (composite > 0)
    comp_v = composite[valid]

    sensitivity_indices: Dict[str, float] = {}

    for removed_key in weights.keys():
        # Recalcul sans la couche avec re-normalisation des poids
        sub_weights = {k: w for k, w in weights.items() if k != removed_key}
        sub_sum = sum(sub_weights.values())
        norm_sub_weights = {k: w / sub_sum for k, w in sub_weights.items()}

        sub_composite = np.zeros_like(mask, dtype=float)
        for k, w in norm_sub_weights.items():
            sub_composite += w * layers[k].astype(float)

        diff = np.abs(composite[valid] - sub_composite[valid]) / comp_v * 100.0
        sensitivity_indices[removed_key] = round(float(np.nanmean(diff)), 2)

    return sensitivity_indices
