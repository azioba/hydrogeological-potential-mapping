"""
Script de mise à jour du notebook principal à la racine pour intégrer les améliorations hydromap.
"""

import json
from pathlib import Path

notebook_file = Path(__file__).resolve().parent.parent / "hydrogeological_potential_mapping.ipynb"

with open(notebook_file, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Cellule 2 : Configuration mise à jour (dynamique, scores Niger par défaut, AHP)
new_config_code = [
    "# ════════════════════════════════════════════════════════════\n",
    "#   CONFIGURATION — Adapt to your study area\n",
    "# ════════════════════════════════════════════════════════════\n",
    "\n",
    "import sys\n",
    "from pathlib import Path\n",
    "\n",
    "# ── Project paths ─────────────────────────────────────────\n",
    "# Détection automatique du répertoire courant du projet\n",
    "ROOT      = Path.cwd()\n",
    "sys.path.append(str(ROOT))\n",
    "\n",
    "DATA_RAW  = ROOT / 'data' / 'raw'\n",
    "DATA_PROC = ROOT / 'data' / 'processed'\n",
    "MAPS      = ROOT / 'outputs' / 'maps'\n",
    "\n",
    "for folder in [DATA_RAW, DATA_PROC, MAPS,\n",
    "               DATA_RAW/'gadm', DATA_RAW/'bgs',\n",
    "               DATA_RAW/'chirps', DATA_RAW/'srtm', DATA_RAW/'wpdx']:\n",
    "    folder.mkdir(parents=True, exist_ok=True)\n",
    "\n",
    "# ── Coordinate Reference System ────────────────────────────\n",
    "# UTM Zone 32N pour le Niger\n",
    "TARGET_CRS = 'EPSG:32632'\n",
    "RES = 1000   # mètres (1 km)\n",
    "\n",
    "# ── Input file paths ───────────────────────────────────────\n",
    "GADM_PATH  = DATA_RAW / 'gadm'   / 'gadm41_NER.gpkg'\n",
    "BGS_PATH   = DATA_RAW / 'bgs'    / 'Niger_HG.shp'\n",
    "CHIRPS_DIR = DATA_RAW / 'chirps'\n",
    "DEM_PATH   = DATA_RAW / 'srtm'   / 'niger_dem.tif'\n",
    "\n",
    "# ── BGS hydrogeology scoring ───────────────────────────────\n",
    "HYDRO_SCORES = {\n",
    "    'CSIF-M/H': 4,  # Grès fracturés sédimentaires productifs élevés\n",
    "    'CSI-M/H' : 3,  # Sédimentaire moyen à élevé\n",
    "    'U-M/H(L)': 3,  # Alluvions / non consolidé\n",
    "    'I-L/M'   : 2,  # Faible à moyen\n",
    "    'B-L'     : 1,  # Socle cristallin (Basement)\n",
    "    'n/a'     : 0,\n",
    "}\n",
    "BGS_CODE_COLUMN = 'NigHGComb'\n",
    "\n",
    "# ── Model weights via AHP (Analytic Hierarchy Process / Saaty) ─\n",
    "from src.hydromap.ahp import AHPModel\n",
    "\n",
    "ahp = AHPModel(\n",
    "    criteria=['geology', 'rainfall', 'slope', 'tpi'],\n",
    "    pairwise_matrix=[\n",
    "        [1.0, 2.0, 3.0, 3.0],\n",
    "        [0.5, 1.0, 2.0, 2.0],\n",
    "        [1/3, 0.5, 1.0, 1.0],\n",
    "        [1/3, 0.5, 1.0, 1.0]\n",
    "    ]\n",
    ")\n",
    "WEIGHTS = ahp.get_weights()\n",
    "print(ahp.summary())\n",
    "\n",
    "# ── GADM layer names ───────────────────────────────────────\n",
    "GADM_COUNTRY = 'ADM_ADM_0'\n",
    "GADM_REGION  = 'ADM_ADM_1'\n",
    "\n",
    "print('✅ Configuration chargée avec succès.')\n",
]

# Cellule 8 : Slope & TPI sans effet de bord
new_terrain_code = [
    "# ── Pente et TPI sans artefacts de bordure ─────────────────\n",
    "from src.hydromap.terrain import compute_slope, compute_tpi\n",
    "\n",
    "# Calcul de pente avec inversion (faible pente = meilleure infiltration)\n",
    "slope, slope_norm = compute_slope(dem_utm, resolution_m=RES, mask=mask, invert=True)\n",
    "\n",
    "with rasterio.open(DATA_PROC / 'layer_slope.tif', 'w', **PROFILE) as dst:\n",
    "    dst.write(slope_norm.astype('float32'), 1)\n",
    "\n",
    "# Calcul du TPI avec filtre ignorant les NaNs (vallées / dépressions = accumulation d'eau)\n",
    "tpi, tpi_norm = compute_tpi(dem_utm, window_size=15, mask=mask, invert=True)\n",
    "\n",
    "with rasterio.open(DATA_PROC / 'layer_tpi.tif', 'w', **PROFILE) as dst:\n",
    "    dst.write(tpi_norm.astype('float32'), 1)\n",
    "\n",
    "print(f'✅ Pente calculée et normalisée (max observée : {np.nanmax(slope):.1f}°)')\n",
    "print(f'✅ TPI calculé sans artefact de bordure (voisinage : 15 km)')\n",
]

# Cellule 10 : Composite GWPI et classification Jenks
new_overlay_code = [
    "# ── Weighted composite score (GWPI) & Classification ──────\n",
    "from src.hydromap.overlay import compute_gwpi, classify_potential, calculate_class_areas\n",
    "\n",
    "layers = {\n",
    "    'geology' : geo_norm,\n",
    "    'rainfall': chirps_norm,\n",
    "    'slope'   : slope_norm,\n",
    "    'tpi'     : tpi_norm,\n",
    "}\n",
    "\n",
    "score = compute_gwpi(layers, WEIGHTS, mask=mask)\n",
    "\n",
    "# Classification par seuils naturels (Fisher-Jenks) pour respecter la réalité hydrogéologique\n",
    "classes, thresholds = classify_potential(score, method='jenks', n_classes=4, mask=mask)\n",
    "\n",
    "with rasterio.open(DATA_PROC / 'score_composite.tif', 'w', **PROFILE) as dst:\n",
    "    dst.write(score.astype('float32'), 1)\n",
    "with rasterio.open(DATA_PROC / 'potentiel_hydro_classes.tif', 'w', **PROFILE) as dst:\n",
    "    dst.write(classes.astype('float32'), 1)\n",
    "\n",
    "print(f'GWPI range  : {np.nanmin(score):.3f} – {np.nanmax(score):.3f}')\n",
    "print(f'Seuils Jenks: {[round(t, 3) for t in thresholds]}')\n",
    "\n",
    "LABELS = {1: 'Faible', 2: 'Modéré', 3: 'Bon', 4: 'Excellent'}\n",
    "areas = calculate_class_areas(classes, resolution_m=RES, labels=LABELS, mask=mask)\n",
    "print('\\nSuperficie par classe (Fisher-Jenks) :')\n",
    "for cls, s in areas.items():\n",
    "    print(f\"  {cls} — {s['label']:<10} : {s['area_km2']:>10,.0f} km²  ({s['percentage']:.1f}%)\")\n",
]

# Remplacement dans les cellules
nb["cells"][2]["source"] = new_config_code
nb["cells"][8]["source"] = new_terrain_code
nb["cells"][10]["source"] = new_overlay_code

with open(notebook_file, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("[OK] hydrogeological_potential_mapping.ipynb mis à jour avec succès.")
