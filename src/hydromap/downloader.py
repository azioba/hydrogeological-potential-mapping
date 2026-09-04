"""
Module d'automatisation du téléchargement des jeux de données ouverts (GADM, CHIRPS, etc.).
"""

from pathlib import Path
from typing import List, Optional
import requests
from tqdm import tqdm


def download_file_with_progress(url: str, destination: Path, chunk_size: int = 1024 * 1024) -> Path:
    """
    Télécharge un fichier distant avec barre de progression interactive.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with open(destination, "wb") as file, tqdm(
        desc=destination.name,
        total=total_size,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=chunk_size):
            size = file.write(data)
            bar.update(size)

    return destination


def download_gadm_country(country_code: str, output_dir: Path) -> Path:
    """
    Télécharge les frontières administratives GADM v4.1 au format GeoPackage.

    :param country_code: Code ISO à 3 lettres (ex: 'NER', 'SEN', 'KEN')
    :param output_dir: Dossier de destination local
    :returns: Chemin du fichier GeoPackage téléchargé
    """
    country_code = country_code.upper()
    filename = f"gadm41_{country_code}.gpkg"
    target_path = output_dir / filename

    if target_path.exists():
        print(f"[OK] GADM déjà présent : {target_path}")
        return target_path

    url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/{filename}"
    print(f"[DOWN] Téléchargement de GADM pour {country_code}...")
    try:
        return download_file_with_progress(url, target_path)
    except Exception as exc:
        print(f"[WARN] Échec du téléchargement direct GADM ({exc}). Rendez-vous sur https://gadm.org/download_country.html")
        raise


def download_chirps_annual(
    years: List[int],
    output_dir: Path,
    region: str = "africa",
) -> List[Path]:
    """
    Télécharge les rasters annuels de précipitations CHIRPS v2.0.

    :param years: Liste des années à télécharger (ex: [2020, 2021, 2022])
    :param output_dir: Dossier de destination local
    :param region: 'africa' ou 'global'
    :returns: Liste des chemins des GeoTIFF téléchargés
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: List[Path] = []

    base_url = (
        f"https://data.chc.ucsb.edu/products/CHIRPS-2.0/{region}_annual/tifs"
    )

    for year in years:
        filename = f"chirps-v2.0.{year}.tif"
        target_path = output_dir / filename

        if target_path.exists():
            print(f"[OK] CHIRPS {year} déjà présent : {target_path}")
            downloaded.append(target_path)
            continue

        url = f"{base_url}/{filename}"
        print(f"[DOWN] Téléchargement CHIRPS {year}...")
        try:
            download_file_with_progress(url, target_path)
            downloaded.append(target_path)
        except Exception as exc:
            print(f"[WARN] Échec pour l'année {year} ({exc})")

    return downloaded
