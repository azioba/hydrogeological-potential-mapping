# 🌍 Hydrogeological Potential Mapping

> **Open-source toolkit for groundwater potential zone mapping at national scale**  
> Built with Python · Open Data Only · Fully Reproducible

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Open Data](https://img.shields.io/badge/data-100%25%20open%20source-green.svg)]()

---

## 📌 What is this?

This repository provides a **complete, reusable Python pipeline** to map groundwater potential zones using the **Weighted Index Overlay (WIO)** method — one of the most widely used approaches in hydrogeological GIS literature.

It was originally developed for **Niger (West Africa)** as a proof-of-concept demonstrating that meaningful hydrogeological analysis can be performed using only free, open-source data. The code is designed to be **adapted to any country** by changing a single configuration section.

**Live demo (Niger):** https://azioba.github.io/niger-hydrogeologie

---

## 🗺️ Example output

| Groundwater Potential Map — Niger |
|:---------------------------------:|
| ![Niger Hydrogeological Map](outputs/maps/06_potentiel_hydrogeologique_niger.png) |

*4-class groundwater potential map at 1km resolution combining geology, rainfall, slope and topographic position.*

---

## ⚡ Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/azioba/hydrogeological-potential-mapping.git
cd hydrogeological-potential-mapping
```

### 2. Install dependencies

```bash
pip install geopandas rasterio rioxarray scipy matplotlib folium rasterstats tqdm requests
```

### 3. Download your data

| Layer | Source | How to get it |
|-------|--------|---------------|
| 🗺️ Administrative boundaries | [GADM](https://gadm.org/download_country.html) | Download `.gpkg` for your country |
| 🪨 Hydrogeology (BGS) | [BGS Africa Groundwater Atlas](https://www.bgs.ac.uk/africagroundwateratlas/) | Free shapefiles per country |
| 🌧️ Rainfall (CHIRPS) | [CHIRPS](https://www.chc.ucsb.edu/data/chirps/) | Annual `.tif` files, Africa or global |
| ⛰️ Digital Elevation Model | [HydroSHEDS](https://www.hydrosheds.org/hydrosheds-core-downloads) | 3 arc-sec DEM, by continent |

Place files in the `data/raw/` folder following the structure below.

### 4. Configure & run

Edit the `⚙️ CONFIGURATION` section at the top of the notebook — change the file paths, your country's UTM CRS, and the BGS hydrogeology codes. Then run all cells.

```
data/
└── raw/
    ├── gadm/        → gadm41_XXX.gpkg
    ├── bgs/         → YourCountry_HG.shp
    ├── chirps/      → chirps-v2.0.YYYY.tif
    └── srtm/        → your_dem.tif
```

---

## 🔬 Methodology

The model computes a **Groundwater Potential Index (GWPI)** using a weighted linear combination of normalized thematic layers:

```
GWPI = Σ (Wᵢ × Nᵢ)
```

where `Wᵢ` is the weight and `Nᵢ` the min-max normalized value of layer `i`.

### Default weights

| Layer | Weight | Hydrogeological rationale |
|-------|--------|--------------------------|
| 🪨 Geology (BGS) | **40%** | Primary control on aquifer presence and productivity |
| 🌧️ Rainfall (CHIRPS) | **25%** | Direct proxy for aquifer recharge |
| ⛰️ Slope (SRTM) | **20%** | Low slope → high infiltration vs runoff |
| 🏔️ TPI | **15%** | Topographic lows → water accumulation zones |

Weights are fully configurable. For data-rich areas, consider calibrating with borehole yield data or using AHP (Analytic Hierarchy Process).

### Classification

The composite score is classified into **4 groundwater potential levels** using quartile thresholds — ensuring equal spatial representation of each class.

| Class | Potential level |
|-------|----------------|
| 4 | 🟢 Excellent |
| 3 | 🟡 Good |
| 2 | 🟠 Moderate |
| 1 | 🔴 Low |

---

## 📓 Notebooks

| Notebook | Description |
|----------|-------------|
| `01_exploration.ipynb` | Data loading, visualization, coverage check |
| `hydrogeological_potential_mapping.ipynb` | **Main notebook** — preprocessing, scoring, classification, output map |
| `03_interactive_map.ipynb` | Folium interactive HTML map with popups |
| `04_comparison_v1_v2.ipynb` | Model comparison when adding new layers |

---

## 🔧 Extending the model

The pipeline is designed to be extended with additional layers:

```python
# Add to WEIGHTS dict — must sum to 1.0
WEIGHTS = {
    'geology'    : 0.35,
    'rainfall'   : 0.22,
    'slope'      : 0.17,
    'tpi'        : 0.11,
    'lineaments' : 0.15,  # ← add GEM faults + DEM gradients
    'ndvi'       : 0.08,  # ← add MODIS or Sentinel-2 NDVI (proxy for soil moisture)
}
```

**Suggested additional layers:**
- **Lineament density** — from [GEM Global Active Faults](https://github.com/GEMScienceTools/gem-global-active-faults) + DEM gradient analysis
- **NDVI** — from [MODIS MOD13A3](https://appeears.earthdatacloud.nasa.gov/) or Sentinel-2 via Google Earth Engine
- **Drainage density** — computed from HydroSHEDS river network
- **Land use / Land cover** — from [ESA WorldCover](https://esa-worldcover.org/)

---

## 🌍 Tested countries

| Country | Status | Notes |
|---------|--------|-------|
| 🇳🇪 Niger | ✅ Complete | Original case study |
| Your country | 🔄 Pending | Open a PR! |

---

## 📚 References

- Andualem & Demeke (2020) — *Groundwater potential mapping using geospatial techniques* — [Cogent Geoscience](https://www.tandfonline.com/doi/full/10.1080/24749508.2020.1728882)
- Hussein et al. (2021) — *Groundwater Potential Zone Mapping Using AHP and GIS* — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8727729/)
- Styron & Pagani (2020) — *The GEM Global Active Faults Database* — [Earthquake Spectra](https://journals.sagepub.com/doi/full/10.1177/8755293020944182)
- BGS Africa Groundwater Atlas — [bgs.ac.uk](https://www.bgs.ac.uk/africagroundwateratlas/)

---

## 👤 Author

**HAMIDOU BÂ Abdoul Aziz**  
Geologist · Product Owner · Data Scientist  


[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://www.linkedin.com/in/azioba)
[![GitHub](https://img.shields.io/badge/GitHub-azioba-black?logo=github)](https://github.com/azioba)

---

## 📄 License

MIT License — Free to use, adapt and share with attribution.  
If you use this code in your research or projects, a citation or mention is appreciated.

```
HAMIDOU BÂ Abdoul Aziz. (2026). Hydrogeological Potential Mapping — Open Source Pipeline.
GitHub: https://github.com/azioba/hydrogeological-potential-mapping
```

---

## 🤝 Contributing

Contributions are welcome — especially:
- Results from new countries (open a PR with your map!)
- Additional data sources or layers
- Validation against borehole data
- Bug fixes and performance improvements

Open an issue or submit a pull request.


