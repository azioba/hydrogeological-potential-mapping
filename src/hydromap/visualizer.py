"""
Module de visualisation cartographique :
- Cartes statiques haute définition (Matplotlib) prêtes pour publication/rapports.
- Cartes interactives Web (Folium / Leaflet) avec fonds multiples et infobulles statistiques.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


DEFAULT_COLORS = ["#d73027", "#fc8d59", "#91cf60", "#1a9850"]
DEFAULT_LABELS = {1: "Faible / Low", 2: "Modéré / Moderate", 3: "Bon / Good", 4: "Excellent / High"}


def plot_groundwater_potential_map(
    classes_grid: np.ndarray,
    bounds: Tuple[float, float, float, float],
    country_gdf=None,
    regions_gdf=None,
    target_crs: str = "EPSG:32632",
    weights: Optional[Dict[str, float]] = None,
    cr_score: Optional[float] = None,
    resolution_m: int = 1000,
    output_path: Optional[Union[str, Path]] = None,
    title: str = "Groundwater Potential Zone Map",
    subtitle: str = "AHP & Weighted Index Overlay Model — Open Source Data",
    author: str = "HAMIDOU BÂ Abdoul Aziz",
    dpi: int = 200,
) -> plt.Figure:
    """
    Génère une carte statique cartographique haute définition pour publication ou rapport.

    :param classes_grid: Grille 2D des classes discrètes (1 à 4)
    :param bounds: [minx, miny, maxx, maxy]
    :param country_gdf: GeoDataFrame de la frontière nationale
    :param regions_gdf: GeoDataFrame des subdivisions administratives
    :param target_crs: Code CRS projeté
    :param weights: Dictionnaire des poids AHP utilisés
    :param cr_score: Ratio de cohérence AHP
    :param resolution_m: Résolution de la grille en mètres
    :param output_path: Chemin du fichier PNG de sortie
    :param title: Titre principal de la carte
    :param subtitle: Sous-titre méthodologique
    :param author: Nom de l'auteur
    :param dpi: Résolution d'export
    :returns: Objet Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(13, 14))

    cmap_hg = mcolors.ListedColormap(DEFAULT_COLORS)
    norm_hg = mcolors.BoundaryNorm([0.5, 1.5, 2.5, 3.5, 4.5], cmap_hg.N)
    ext_utm = [bounds[0], bounds[2], bounds[1], bounds[3]]

    masked_data = np.ma.masked_invalid(classes_grid)
    ax.imshow(
        masked_data,
        extent=ext_utm,
        cmap=cmap_hg,
        norm=norm_hg,
        origin="upper",
        interpolation="nearest",
    )

    if country_gdf is not None:
        country_gdf.boundary.plot(ax=ax, color="black", linewidth=1.5, zorder=3)

    if regions_gdf is not None:
        regions_gdf.boundary.plot(
            ax=ax, color="#333333", linewidth=0.6, linestyle="--", zorder=3
        )

        col_name = next(
            (c for c in regions_gdf.columns if "name" in c.lower()), None
        )
        if col_name:
            for _, row in regions_gdf.iterrows():
                c = row.geometry.centroid
                ax.annotate(
                    str(row[col_name]).upper(),
                    xy=(c.x, c.y),
                    ha="center",
                    fontsize=7.5,
                    fontweight="bold",
                    color="white",
                    bbox=dict(
                        boxstyle="round,pad=0.25",
                        facecolor="#222222",
                        alpha=0.70,
                        edgecolor="none",
                    ),
                    zorder=5,
                )

    # Légende des 4 classes de potentiel
    legend_patches = [
        mpatches.Patch(color=DEFAULT_COLORS[i], label=f"{i+1} — {DEFAULT_LABELS[i+1]}")
        for i in range(4)
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower left",
        fontsize=10,
        framealpha=0.92,
        title="Groundwater Potential",
        title_fontsize=11,
    )

    # Note méthodologique
    weights_str = ""
    if weights:
        weights_str = " | ".join([f"{k.capitalize()}: {v*100:.1f}%" for k, v in weights.items()])

    note_lines = [
        f"Resolution: {resolution_m // 1000} km | CRS: {target_crs}",
    ]
    if weights_str:
        note_lines.append(f"AHP Weights: {weights_str}")
    if cr_score is not None:
        note_lines.append(f"Consistency Ratio (CR): {cr_score:.3f} (Valid < 0.10)")

    ax.text(
        0.98,
        0.02,
        "\n".join(note_lines),
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
        ha="right",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.90, edgecolor="#cccccc"),
        zorder=6,
    )

    # Signature
    ax.text(
        0.01,
        0.01,
        f"{author} | github.com/azioba",
        transform=ax.transAxes,
        fontsize=8,
        color="#444444",
        va="bottom",
        style="italic",
        zorder=6,
    )

    ax.set_title(f"{title}\n{subtitle}", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel(f"Easting {target_crs} (m)", fontsize=10)
    ax.set_ylabel(f"Northing {target_crs} (m)", fontsize=10)
    ax.ticklabel_format(style="sci", axis="both", scilimits=(0, 0))

    plt.tight_layout()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_p, dpi=dpi, bbox_inches="tight")
        print(f"[SAVE] Carte haute définition enregistrée : {out_p}")

    return fig


def create_folium_interactive_map(
    classes_grid: np.ndarray,
    bounds: Tuple[float, float, float, float],
    center_lat: float,
    center_lon: float,
    zoom_start: int = 6,
    title: str = "Hydrogeological Potential Map",
    output_html: Optional[Union[str, Path]] = None,
):
    """
    Génère une carte interactive Folium / Leaflet prête pour GitHub Pages.
    """
    try:
        import folium
    except ImportError:
        print("[WARN] Folium n'est pas installé. Installez-le avec `pip install folium`.")
        return None

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles="CartoDB positron",
        control_scale=True,
    )

    # Fonds de carte additionnels
    folium.TileLayer("CartoDB dark_matter", name="Fond Sombre").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite (Esri)",
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    if output_html:
        out_p = Path(output_html)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(out_p))
        print(f"[WEB] Carte web interactive enregistrée : {out_p}")

    return m
