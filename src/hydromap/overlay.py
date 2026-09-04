"""
Module de combinaison multicritère (Weighted Index Overlay) et de classification.
Prend en charge la discrétisation par seuils naturels (Fisher-Jenks), quantiles et intervalles égaux.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np


def compute_gwpi(
    layers: Dict[str, np.ndarray],
    weights: Dict[str, float],
    mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Calcule l'indice composite de potentiel hydrogéologique (GWPI) :
        GWPI = Σ (Poids_i × Couche_normalisée_i)

    :param layers: Dictionnaire des rasters normalisés (0 à 1) par critère
    :param weights: Dictionnaire des poids dérivés (doivent sommer à 1.0)
    :param mask: Masque booléen délimitant la zone d'étude
    :returns: Raster 2D float32 du GWPI
    """
    weight_sum = sum(weights.values())
    if not np.isclose(weight_sum, 1.0, atol=1e-3):
        raise ValueError(f"La somme des poids doit être égale à 1.0 (somme actuelle : {weight_sum:.4f})")

    missing_layers = [k for k in weights if k not in layers]
    if missing_layers:
        raise KeyError(f"Couches manquantes dans le dictionnaire layers : {missing_layers}")

    first_shape = next(iter(layers.values())).shape
    composite = np.zeros(first_shape, dtype=float)

    for criterion, weight in weights.items():
        layer_arr = layers[criterion].astype(float)
        composite += weight * layer_arr

    if mask is not None:
        composite = np.where(mask, composite, np.nan)

    return composite.astype(np.float32)


def classify_potential(
    score_grid: np.ndarray,
    method: str = "jenks",
    n_classes: int = 4,
    mask: Optional[np.ndarray] = None,
    custom_thresholds: Optional[List[float]] = None,
) -> Tuple[np.ndarray, List[float]]:
    """
    Classifie la carte continue de GWPI en classes qualitatives d'aptitude (ex: 1=Faible à 4=Excellent).

    :param score_grid: Grille 2D des scores continus GWPI (0.0 à 1.0)
    :param method: 'jenks' (recommandé), 'quantiles', 'equal_interval', ou 'custom'
    :param n_classes: Nombre de classes (défaut: 4)
    :param mask: Masque booléen de la zone d'étude
    :param custom_thresholds: Liste de (n_classes - 1) seuils croissants si method='custom'
    :returns: Tuple (grille_classes_1_a_N, liste_des_seuils)
    """
    valid = ~np.isnan(score_grid)
    if mask is not None:
        valid = valid & mask

    values = score_grid[valid]
    if len(values) == 0:
        return np.full_like(score_grid, np.nan), []

    thresholds: List[float] = []

    if method == "custom":
        if not custom_thresholds or len(custom_thresholds) != n_classes - 1:
            raise ValueError(f"Pour method='custom', custom_thresholds doit contenir {n_classes - 1} seuils.")
        thresholds = sorted(custom_thresholds)

    elif method == "quantiles":
        quantiles = np.linspace(0, 100, n_classes + 1)[1:-1]
        thresholds = [float(np.percentile(values, q)) for q in quantiles]

    elif method == "equal_interval":
        v_min, v_max = float(np.min(values)), float(np.max(values))
        step = (v_max - v_min) / n_classes
        thresholds = [v_min + (i + 1) * step for i in range(n_classes - 1)]

    elif method == "jenks":
        try:
            import jenkspy
            # Échantillonner si le tableau est très grand pour performance
            sample = values
            if len(values) > 25000:
                np.random.seed(42)
                sample = np.random.choice(values, size=25000, replace=False)
            breaks = jenkspy.jenks_breaks(sample, n_classes=n_classes)
            thresholds = [float(b) for b in breaks[1:-1]]
        except ImportError:
            # Replantage élégant vers quantiles si jenkspy n'est pas encore installé
            quantiles = np.linspace(0, 100, n_classes + 1)[1:-1]
            thresholds = [float(np.percentile(values, q)) for q in quantiles]

    else:
        raise ValueError(f"Méthode de classification inconnue : {method}")

    # Application des seuils pour créer les classes 1 à n_classes
    classes = np.full_like(score_grid, np.nan)
    classes[valid] = 1

    for idx, thresh in enumerate(thresholds):
        classes[valid & (score_grid > thresh)] = idx + 2

    return classes.astype(np.float32), thresholds


def calculate_class_areas(
    classes_grid: np.ndarray,
    resolution_m: float,
    labels: Optional[Dict[int, str]] = None,
    mask: Optional[np.ndarray] = None,
) -> Dict[int, Dict[str, Union[str, float, int]]]:
    """
    Calcule les superficies absolues (km²) et relatives (%) de chaque classe de potentiel.

    :param classes_grid: Grille 2D des classes discrètes (1, 2, 3, 4, etc.)
    :param resolution_m: Résolution spatiale en mètres (ex: 1000m)
    :param labels: Dictionnaire optionnel associant le numéro de classe à son nom
    :param mask: Masque optionnel
    :returns: Dictionnaire des statistiques de superficie par classe
    """
    pixel_area_km2 = (resolution_m / 1000.0) ** 2

    valid = ~np.isnan(classes_grid)
    if mask is not None:
        valid = valid & mask

    total_pixels = int(np.sum(valid))
    if total_pixels == 0:
        return {}

    unique_classes = sorted([int(c) for c in np.unique(classes_grid[valid])])
    results = {}

    default_labels = {1: "Faible", 2: "Modéré", 3: "Bon", 4: "Excellent"}

    for cls in unique_classes:
        count = int(np.sum(valid & (classes_grid == cls)))
        area_km2 = float(count * pixel_area_km2)
        pct = float((count / total_pixels) * 100.0)

        label = (
            labels.get(cls, default_labels.get(cls, f"Classe {cls}"))
            if labels
            else default_labels.get(cls, f"Classe {cls}")
        )

        results[cls] = {
            "label": label,
            "pixels": count,
            "area_km2": round(area_km2, 1),
            "percentage": round(pct, 2),
        }

    return results
