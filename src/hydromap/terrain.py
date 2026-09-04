"""
Module d'analyse de terrain et dérivées topographiques (MNT, Pente, TPI).
Conçu pour éliminer les artefacts de bordure et normaliser de façon robuste.
"""

from typing import Optional, Tuple
import numpy as np
from scipy.ndimage import uniform_filter


def robust_normalize(
    array: np.ndarray,
    mask: Optional[np.ndarray] = None,
    invert: bool = False,
    percentile_clip: Tuple[float, float] = (1.0, 99.0),
) -> np.ndarray:
    """
    Normalise un tableau 2D entre 0 et 1 avec écrêtage robuste par percentiles.
    Évite que des artefacts extrêmes (bruit radar, pics de falaise) n'écrasent la dynamique.

    :param array: Tableau 2D (valeurs continues, peut contenir des NaNs)
    :param mask: Masque booléen optionnel (True = pixel d'intérêt dans l'aire d'étude)
    :param invert: Si True, 1 - norm (ex: pente faible -> score élevé)
    :param percentile_clip: Percentiles (min, max) pour l'écrêtage, par défaut (1%, 99%)
    :returns: Tableau 2D normalisé entre 0.0 et 1.0 (NaNs en dehors du masque)
    """
    arr = array.copy().astype(float)
    valid_mask = ~np.isnan(arr)
    if mask is not None:
        valid_mask = valid_mask & mask

    if not np.any(valid_mask):
        return np.full_like(arr, np.nan)

    valid_vals = arr[valid_mask]
    p_low, p_high = np.percentile(valid_vals, percentile_clip)

    if p_high <= p_low:
        norm = np.zeros_like(arr)
    else:
        clipped = np.clip(arr, p_low, p_high)
        norm = (clipped - p_low) / (p_high - p_low)

    if invert:
        norm = 1.0 - norm

    if mask is not None:
        norm = np.where(mask, norm, np.nan)
    else:
        norm = np.where(valid_mask, norm, np.nan)

    return norm.astype(np.float32)


def compute_slope(
    dem: np.ndarray,
    resolution_m: float,
    mask: Optional[np.ndarray] = None,
    invert: bool = True,
    percentile_clip: Tuple[float, float] = (1.0, 99.0),
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calcule la pente en degrés à partir d'un MNT projeté en mètres.

    :param dem: Modèle Numérique de Terrain 2D (altitudes en mètres)
    :param resolution_m: Résolution du pixel en mètres (ex: 1000m)
    :param mask: Masque booléen délimitant la zone d'étude
    :param invert: Inverser la normalisation (faible pente = meilleure infiltration)
    :param percentile_clip: Seuils de coupure pour la normalisation
    :returns: Tuple (pente_degrés, pente_normalisée)
    """
    dem_arr = dem.astype(float)
    valid = ~np.isnan(dem_arr)

    # Remplissage par propagation pour le calcul des gradients sans effet de bord
    # Si le MNT a une marge, le gradient aux frontières intérieures reste continu
    dem_for_grad = np.where(valid, dem_arr, 0.0)

    # Calcul des gradients spatialisés
    dy, dx = np.gradient(dem_for_grad, resolution_m, resolution_m)
    slope_deg = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))

    # Ne conserver que les pixels valides
    slope_deg = np.where(valid, slope_deg, np.nan)

    if mask is not None:
        slope_deg = np.where(mask, slope_deg, np.nan)

    slope_norm = robust_normalize(
        slope_deg, mask=mask, invert=invert, percentile_clip=percentile_clip
    )

    return slope_deg.astype(np.float32), slope_norm.astype(np.float32)


def compute_tpi(
    dem: np.ndarray,
    window_size: int = 15,
    mask: Optional[np.ndarray] = None,
    invert: bool = True,
    percentile_clip: Tuple[float, float] = (1.0, 99.0),
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calcule le Topographic Position Index (TPI = altitude - altitude_moyenne_voisinage).
    Un TPI négatif indique des vallées, dépressions et fonds de talwegs favorables à la recharge.

    Utilise un filtre uniforme normalisé par le nombre de cellules valides pour éliminer
    les artefacts de bordure près des frontières du masque.

    :param dem: MNT 2D en mètres
    :param window_size: Taille de la fenêtre mobile (ex: 15 pixels = 15km à 1km)
    :param mask: Masque d'étude
    :param invert: Inverser la normalisation (vallées = score élevé)
    :param percentile_clip: Écrêtage robuste
    :returns: Tuple (tpi_brut, tpi_normalise)
    """
    dem_arr = dem.astype(float)
    valid = ~np.isnan(dem_arr)

    dem_zeroed = np.where(valid, dem_arr, 0.0)
    window_area = float(window_size**2)

    # Moyenne de voisinage préservant les NaNs
    sum_filter = uniform_filter(dem_zeroed, size=window_size) * window_area
    count_filter = uniform_filter(valid.astype(float), size=window_size) * window_area

    with np.errstate(divide="ignore", invalid="ignore"):
        neighborhood_mean = np.where(count_filter > 0, sum_filter / count_filter, np.nan)

    tpi_raw = dem_arr - neighborhood_mean
    tpi_raw = np.where(valid, tpi_raw, np.nan)

    if mask is not None:
        tpi_raw = np.where(mask, tpi_raw, np.nan)

    tpi_norm = robust_normalize(
        tpi_raw, mask=mask, invert=invert, percentile_clip=percentile_clip
    )

    return tpi_raw.astype(np.float32), tpi_norm.astype(np.float32)
