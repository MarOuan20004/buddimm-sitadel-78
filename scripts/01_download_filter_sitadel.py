#!/usr/bin/env python3
"""
scripts/01_download_filter_sitadel.py
Buddimm - Cas d'étude Sitadel Yvelines (78)

Étape 1 : Ingestion, filtrage et standardisation des autorisations d'urbanisme
pour le département des Yvelines (78), restreintes aux Personnes Morales.

Sources :
- SDES / DiDo - Ministère de la Transition Écologique
  Licence Ouverte 2.0 (Etalab)
"""

import os
import sys
import json
import logging
import requests
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("sitadel_filter")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")

# URLs officielles DiDo avec filtre serveur DEP_CODE=eq:78
URL_LOGEMENTS = (
    "https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/"
    "8b35affb-55fc-4c1f-915b-7750f974446a/csv?DEP_CODE=eq:78"
)
URL_LOCAUX = (
    "https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/"
    "f8f0700f-806c-40a7-83b1-f21cf507e7c4/csv?DEP_CODE=eq:78"
)

RAW_LOGEMENTS_PATH = os.path.join(DATA_DIR, "sitadel_logements_78.csv")
RAW_LOCAUX_PATH = os.path.join(DATA_DIR, "sitadel_locaux_78.csv")
CLEANED_OUTPUT_PATH = os.path.join(DATA_DIR, "sitadel_78_personnes_morales.csv")
STATS_OUTPUT_PATH = os.path.join(OUTPUTS_DIR, "stats_ingestion_78.json")


def ensure_data_downloaded():
    """Télécharge les données depuis DiDo si elles ne sont pas déjà présentes localement."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    files_to_download = [
        ("Logements 78", URL_LOGEMENTS, RAW_LOGEMENTS_PATH),
        ("Locaux non résidentiels 78", URL_LOCAUX, RAW_LOCAUX_PATH),
    ]

    for label, url, dest_path in files_to_download:
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
            logger.info(f"Fichier déjà présent : {dest_path} ({os.path.getsize(dest_path) / 1e6:.2f} Mo)")
            continue

        logger.info(f"Téléchargement de {label} via l'API DiDo...")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        logger.info(f"Téléchargement terminé : {dest_path} ({os.path.getsize(dest_path) / 1e6:.2f} Mo)")


def normalize_siren(val):
    """Normalise un SIREN au format standardisé 9 chiffres (string)."""
    if pd.isna(val) or val is None or str(val).strip() == "" or str(val).strip().lower() == "nan":
        return None
    val_str = str(val).split(".")[0].strip()
    digits = "".join(ch for ch in val_str if ch.isdigit())
    if len(digits) == 9:
        return digits
    elif len(digits) > 0 and len(digits) < 9:
        return digits.zfill(9)
    return digits if digits else None


def clean_and_filter():
    """Charge, audite et filtre les données Sitadel pour les personnes morales du 78."""
    logger.info("Chargement des fichiers CSV Sitadel 78...")
    df_log = pd.read_csv(RAW_LOGEMENTS_PATH, sep=";", low_memory=False)
    df_loc = pd.read_csv(RAW_LOCAUX_PATH, sep=";", low_memory=False)

    total_log = len(df_log)
    total_loc = len(df_loc)
    logger.info(f"Lignes brutes Logements 78 : {total_log}")
    logger.info(f"Lignes brutes Locaux 78 : {total_loc}")

    # Détection personnes morales vs physiques
    # Dans Sitadel, les personnes physiques ont DENOM_DEM et SIREN_DEM vides (RGPD)
    mask_pm_log = df_log["DENOM_DEM"].notna() | df_log["SIREN_DEM"].notna() | df_log["CJ_DEM"].notna()
    mask_pm_loc = df_loc["DENOM_DEM"].notna() | df_loc["SIREN_DEM"].notna() | df_loc["CJ_DEM"].notna()

    pm_log_count = int(mask_pm_log.sum())
    pm_loc_count = int(mask_pm_loc.sum())

    logger.info(f"Personnes morales Logements : {pm_log_count} / {total_log} ({pm_log_count / total_log * 100:.1f}%)")
    logger.info(f"Personnes morales Locaux : {pm_loc_count} / {total_loc} ({pm_loc_count / total_loc * 100:.1f}%)")

    # Filtrer strictement sur personnes morales
    df_log_pm = df_log[mask_pm_log].copy()
    df_loc_pm = df_loc[mask_pm_loc].copy()

    df_log_pm["VOLET_SITADEL"] = "LOGEMENT"
    df_loc_pm["VOLET_SITADEL"] = "LOCAL"

    # Harmonisation des colonnes communes
    cols_communes = [
        "NUM_DAU", "TYPE_DAU", "ETAT_DAU", "COMM", "DEP_CODE",
        "DATE_REELLE_AUTORISATION", "DATE_REELLE_DOC", "DATE_REELLE_DAACT",
        "AN_DEPOT", "DR_DEPOT", "DPC_AUT", "DPC_DOC", "DPC_DERN",
        "APE_DEM", "CJ_DEM", "DENOM_DEM", "SIREN_DEM", "SIRET_DEM",
        "CODPOST_DEM", "LOCALITE_DEM", "VOLET_SITADEL"
    ]

    # Spécificités Logements
    cols_log_specifiques = [
        "RESIDENCE", "RES_PERS_AGEES", "RES_ETUDIANTS", "RES_TOURISME",
        "RES_HOTEL_SOCIALE", "RES_SOCIALE", "RES_HANDICAPES", "RES_AUTRE",
        "NB_LGT_TOT_CREES", "NB_LGT_IND_CREES", "NB_LGT_COL_CREES",
        "NB_LGT_PRET_LOC_SOCIAL", "SURF_HAB_CREEE"
    ]

    # Spécificités Locaux
    cols_loc_specifiques = [
        "DESTINATION_PRINCIPALE", "TYPE_SERVICE_PUBLIC",
        "SURF_HEB_CREEE", "SURF_PUB_CREEE", "SURF_BUR_CREEE",
        "SURF_COM_CREEE", "SURF_IND_CREEE", "SURF_LOC_CREEE"
    ]

    # Aligner les colonnes pour la concaténation
    for col in cols_loc_specifiques:
        if col not in df_log_pm.columns:
            df_log_pm[col] = np.nan

    for col in cols_log_specifiques:
        if col not in df_loc_pm.columns:
            df_loc_pm[col] = np.nan

    all_cols = cols_communes + [c for c in cols_log_specifiques + cols_loc_specifiques if c not in cols_communes]

    df_merged = pd.concat([df_log_pm[all_cols], df_loc_pm[all_cols]], ignore_index=True)
    logger.info(f"Total autorisations Personnes Morales combinées : {len(df_merged)}")

    # Normalisation du SIREN
    df_merged["SIREN_CLEAN"] = df_merged["SIREN_DEM"].apply(normalize_siren)
    missing_siren = df_merged["SIREN_CLEAN"].isna().sum()
    unique_sirens = df_merged["SIREN_CLEAN"].dropna().nunique()

    logger.info(f"SIRENs normalisés uniques : {unique_sirens}")
    logger.info(f"Lignes avec SIREN manquant/invalide : {missing_siren} ({missing_siren / len(df_merged) * 100:.2f}%)")

    # Nettoyage et normalisation de la dénomination
    df_merged["DENOM_CLEAN"] = (
        df_merged["DENOM_DEM"]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"NAN": None, "NONE": None, "": None})
    )

    # Conversion propre des dates
    for date_col in ["DATE_REELLE_AUTORISATION", "DATE_REELLE_DOC", "DATE_REELLE_DAACT"]:
        df_merged[date_col] = pd.to_datetime(df_merged[date_col], errors="coerce")

    # Année d'autorisation
    df_merged["ANNEE_AUTORISATION"] = df_merged["DATE_REELLE_AUTORISATION"].dt.year
    df_merged["ANNEE_AUTORISATION"] = df_merged["ANNEE_AUTORISATION"].fillna(df_merged["AN_DEPOT"])

    # Sauvegarde CSV
    df_merged.to_csv(CLEANED_OUTPUT_PATH, index=False, sep=";")
    logger.info(f"Fichier nettoyé exporté dans : {CLEANED_OUTPUT_PATH} ({os.path.getsize(CLEANED_OUTPUT_PATH) / 1e6:.2f} Mo)")

    # Statistiques d'ingestion exportées en JSON
    stats = {
        "departement": "78 - Yvelines",
        "source": "Sitadel (DiDo / SDES Ministère Transition Écologique)",
        "licence": "Licence Ouverte 2.0 (Etalab)",
        "volumetrie_brute": {
            "total_lignes_logements": total_log,
            "total_lignes_locaux": total_loc,
            "total_lignes_cumulees": total_log + total_loc
        },
        "filtrage_personnes_morales": {
            "permis_logements_pm": pm_log_count,
            "ratio_pm_logements": round(pm_log_count / total_log, 4),
            "permis_locaux_pm": pm_loc_count,
            "ratio_pm_locaux": round(pm_loc_count / total_loc, 4),
            "total_permis_pm": len(df_merged)
        },
        "qualite_donnees": {
            "sirens_uniques": unique_sirens,
            "lignes_siren_manquant": int(missing_siren),
            "taux_completude_siren": round(1 - missing_siren / len(df_merged), 4),
            "taux_completude_cj": round(df_merged["CJ_DEM"].notna().mean(), 4),
            "taux_completude_ape": round(df_merged["APE_DEM"].notna().mean(), 4)
        },
        "repartition_volet": {
            "LOGEMENT": int((df_merged["VOLET_SITADEL"] == "LOGEMENT").sum()),
            "LOCAL": int((df_merged["VOLET_SITADEL"] == "LOCAL").sum())
        },
        "annees_couvertes": {
            "min": int(df_merged["ANNEE_AUTORISATION"].dropna().min()),
            "max": int(df_merged["ANNEE_AUTORISATION"].dropna().max())
        }
    }

    with open(STATS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    logger.info(f"Statistiques d'ingestion sauvegardées dans : {STATS_OUTPUT_PATH}")

    return df_merged, stats


if __name__ == "__main__":
    ensure_data_downloaded()
    clean_and_filter()
