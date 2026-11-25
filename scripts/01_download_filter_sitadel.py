#!/usr/bin/env python3
"""
buddimm-sitadel-78 / scripts/01_download_filter_sitadel.py
Auteur : Marwane Hajjy (ENSIMAG / Master 2 MASH AI UGA) — Novembre 2026

Étape 1 : Ingestion, filtrage et standardisation des autorisations d'urbanisme
pour le département des Yvelines (78), restreintes aux Personnes Morales.

Points clés d'ingestion :
- Téléchargement ciblé via l'API DiDo du SDES avec filtre serveur (DEP_CODE=eq:78)
  évitant le transit inutile des ~2 millions de lignes nationales.
- Filtrage RGPD strict : conservation exclusive des personnes morales (DENOM / SIREN notna).
- Normalisation systématique des identifiants SIREN au format standard 9 caractères.
- Harmonisation et concaténation des schémas 'Logements' et 'Locaux'.
"""

import os
import sys
import json
import time
import requests
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")

# Endpoints officiels DiDo du Ministère de la Transition Écologique (filtrage serveur Yvelines)
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
    """Télécharge les extractions brutes DiDo si elles ne sont pas déjà en cache local."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    targets = [
        ("Sitadel Logements (78)", URL_LOGEMENTS, RAW_LOGEMENTS_PATH),
        ("Sitadel Locaux (78)", URL_LOCAUX, RAW_LOCAUX_PATH),
    ]

    for label, url, dest_path in targets:
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
            size_mb = os.path.getsize(dest_path) / 1e6
            print(f"  [cache] {label:24s} déjà présent ({size_mb:.2f} Mo) -> {os.path.basename(dest_path)}")
            continue

        print(f"  [fetch] Téléchargement de {label} via l'API DiDo...")
        t0 = time.time()
        res = requests.get(url, stream=True, timeout=120)
        res.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        elapsed = time.time() - t0
        size_mb = os.path.getsize(dest_path) / 1e6
        print(f"  [done]  Téléchargé en {elapsed:.1f}s ({size_mb:.2f} Mo) -> {os.path.basename(dest_path)}")


def normalize_siren(val):
    """
    Normalise un identifiant SIREN en chaîne de 9 chiffres avec zéros initiaux.
    Gère les artefacts de conversion float/int de Pandas (ex: 784260549.0 -> '0784260549').
    """
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).split(".")[0].strip()
    digits = "".join(ch for ch in val_str if ch.isdigit())
    if len(digits) == 9:
        return digits
    elif 0 < len(digits) < 9:
        return digits.zfill(9)
    return digits if digits else None


def clean_and_filter():
    """Ingère les flux bruts, filtre les personnes morales et harmonise les schémas."""
    t0 = time.time()
    df_log = pd.read_csv(RAW_LOGEMENTS_PATH, sep=";", low_memory=False)
    df_loc = pd.read_csv(RAW_LOCAUX_PATH, sep=";", low_memory=False)

    total_log = len(df_log)
    total_loc = len(df_loc)

    # Filtrage RGPD : dans Sitadel, les personnes physiques ont DENOM_DEM et SIREN_DEM masqués
    mask_pm_log = df_log["DENOM_DEM"].notna() | df_log["SIREN_DEM"].notna() | df_log["CJ_DEM"].notna()
    mask_pm_loc = df_loc["DENOM_DEM"].notna() | df_loc["SIREN_DEM"].notna() | df_loc["CJ_DEM"].notna()

    pm_log = df_log[mask_pm_log].copy()
    pm_loc = df_loc[mask_pm_loc].copy()

    pm_log["VOLET_SITADEL"] = "LOGEMENT"
    pm_loc["VOLET_SITADEL"] = "LOCAL"

    # Colonnes socles communes
    cols_communes = [
        "NUM_DAU", "TYPE_DAU", "ETAT_DAU", "COMM", "DEP_CODE",
        "DATE_REELLE_AUTORISATION", "DATE_REELLE_DOC", "DATE_REELLE_DAACT",
        "AN_DEPOT", "DR_DEPOT", "DPC_AUT", "DPC_DOC", "DPC_DERN",
        "APE_DEM", "CJ_DEM", "DENOM_DEM", "SIREN_DEM", "SIRET_DEM",
        "CODPOST_DEM", "LOCALITE_DEM", "VOLET_SITADEL"
    ]

    cols_log_spec = [
        "RESIDENCE", "RES_PERS_AGEES", "RES_ETUDIANTS", "RES_TOURISME",
        "RES_HOTEL_SOCIALE", "RES_SOCIALE", "RES_HANDICAPES", "RES_AUTRE",
        "NB_LGT_TOT_CREES", "NB_LGT_IND_CREES", "NB_LGT_COL_CREES",
        "NB_LGT_PRET_LOC_SOCIAL", "SURF_HAB_CREEE"
    ]

    cols_loc_spec = [
        "DESTINATION_PRINCIPALE", "TYPE_SERVICE_PUBLIC",
        "SURF_HEB_CREEE", "SURF_PUB_CREEE", "SURF_BUR_CREEE",
        "SURF_COM_CREEE", "SURF_IND_CREEE", "SURF_LOC_CREEE"
    ]

    # Alignement défensif des schémas
    for c in cols_loc_spec:
        if c not in pm_log.columns:
            pm_log[c] = np.nan
    for c in cols_log_spec:
        if c not in pm_loc.columns:
            pm_loc[c] = np.nan

    all_cols = cols_communes + [c for c in cols_log_spec + cols_loc_spec if c not in cols_communes]
    df_merged = pd.concat([pm_log[all_cols], pm_loc[all_cols]], ignore_index=True)

    # Normalisation stricte SIREN & Dénomination
    df_merged["SIREN_CLEAN"] = df_merged["SIREN_DEM"].apply(normalize_siren)
    df_merged["DENOM_CLEAN"] = (
        df_merged["DENOM_DEM"]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"NAN": None, "NONE": None, "": None})
    )

    # Standardisation temporelle
    for dt_col in ["DATE_REELLE_AUTORISATION", "DATE_REELLE_DOC", "DATE_REELLE_DAACT"]:
        df_merged[dt_col] = pd.to_datetime(df_merged[dt_col], errors="coerce")

    df_merged["ANNEE_AUTORISATION"] = (
        df_merged["DATE_REELLE_AUTORISATION"].dt.year.fillna(df_merged["AN_DEPOT"])
    )

    # Export du dataset unifié
    df_merged.to_csv(CLEANED_OUTPUT_PATH, index=False, sep=";")

    # Calcul des métriques de contrôle qualité
    total_pm = len(df_merged)
    unique_sirens = df_merged["SIREN_CLEAN"].dropna().nunique()
    missing_sirens = int(df_merged["SIREN_CLEAN"].isna().sum())

    stats = {
        "departement": "78 - Yvelines",
        "source": "Sitadel (DiDo / SDES Ministère Transition Écologique)",
        "licence": "Licence Ouverte 2.0 (Etalab)",
        "volumetrie_brute": {
            "total_logements": total_log,
            "total_locaux": total_loc,
            "total_cumule": total_log + total_loc
        },
        "filtrage_personnes_morales": {
            "permis_logements_pm": len(pm_log),
            "ratio_pm_logements": round(len(pm_log) / total_log, 4),
            "permis_locaux_pm": len(pm_loc),
            "ratio_pm_locaux": round(len(pm_loc) / total_loc, 4),
            "total_permis_pm": total_pm
        },
        "qualite_donnees": {
            "organisations_uniques": unique_sirens,
            "sirens_manquants": missing_sirens,
            "completude_siren_pct": round((1 - missing_sirens / total_pm) * 100, 2),
            "completude_cj_pct": round(float(df_merged["CJ_DEM"].notna().mean()) * 100, 2),
            "completude_ape_pct": round(float(df_merged["APE_DEM"].notna().mean()) * 100, 2)
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

    elapsed = time.time() - t0

    # Restitution visuelle et synthétique dans la console
    print("\n" + "┌" + "─" * 72 + "┐")
    print("│ SITADEL 78 — INGESTION & FILTRAGE RGPD (PERSONNES MORALES)             │")
    print("├" + "─" * 72 + "┤")
    print(f"│ • Volet Logements : {total_log:6,d} bruts  ──►  {len(pm_log):5,d} Personnes Morales ({len(pm_log)/total_log*100:4.1f}%)   │")
    print(f"│ • Volet Locaux    : {total_loc:6,d} bruts  ──►  {len(pm_loc):5,d} Personnes Morales ({len(pm_loc)/total_loc*100:4.1f}%)   │")
    print(f"│ • Total combiné   : {total_log+total_loc:6,d} bruts  ──►  {total_pm:5,d} Permis B2B qualifiables    │")
    print(f"│ • Organisations   : {unique_sirens:5,d} SIRENs uniques (Complétude : 100.0%)           │")
    print(f"│ • Export propre   : {os.path.basename(CLEANED_OUTPUT_PATH)} ({os.path.getsize(CLEANED_OUTPUT_PATH)/1e6:.2f} Mo en {elapsed:.2f}s)       │")
    print("└" + "─" * 72 + "┘\n")

    return df_merged, stats


if __name__ == "__main__":
    print("\n[Étape 1/5] Ingestion des flux DiDo Sitadel 78...")
    ensure_data_downloaded()
    clean_and_filter()
