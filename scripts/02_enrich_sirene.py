#!/usr/bin/env python3
"""
scripts/02_enrich_sirene.py
Buddimm - Cas d'étude Sitadel Yvelines (78)

Étape 2 : Enrichissement des demandeurs Personnes Morales via l'API Recherche d'Entreprises
(Annuaire des Entreprises / DINUM / Insee) et réconciliation avec les données Sitadel.

Récupère :
- Catégorie juridique officielle (CJ)
- Code APE / NAF officiel
- Catégorie d'entreprise (PME, ETI, GE)
- Tranche d'effectif salarié
- Statut actif/cessé
- Commune et CP du siège
- Flags médico-sociaux et ESS : est_ess, est_finess, type_siae (ESAT/EA), est_association

Gère un cache local JSON persistant, un mode offline/fallback gracieux, et le typage strict des SIRENs (str).
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("sirene_enrich")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")

INPUT_CLEANED_PATH = os.path.join(DATA_DIR, "sitadel_78_personnes_morales.csv")
ENRICHED_OUTPUT_PATH = os.path.join(DATA_DIR, "sitadel_78_enriched.csv")
CACHE_PATH = os.path.join(DATA_DIR, "cache_sirene.json")
STATS_OUTPUT_PATH = os.path.join(OUTPUTS_DIR, "stats_enrichment_sirene.json")

API_URL = "https://recherche-entreprises.api.gouv.fr/search"


def load_cache():
    """Charge le cache JSON local des requêtes SIRENE."""
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            logger.info(f"Cache SIRENE chargé : {len(cache)} entrées existantes.")
            return cache
        except Exception as e:
            logger.warning(f"Erreur chargement cache : {e}. Nouveau cache initialisé.")
            return {}
    return {}


def save_cache(cache):
    """Sauvegarde le cache JSON de manière atomique."""
    tmp_path = CACHE_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, CACHE_PATH)


def query_api_siren(siren, session):
    """Interroge l'API recherche-entreprises pour un SIREN donné avec gestion des retries."""
    url = f"{API_URL}?q={siren}"
    for attempt in range(2):
        try:
            r = session.get(url, timeout=4)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                if results:
                    first = results[0]
                    complements = first.get("complements", {})
                    siege = first.get("siege", {})

                    return {
                        "found": True,
                        "nom_officiel": first.get("nom_complet"),
                        "cj_sirene": first.get("nature_juridique"),
                        "ape_sirene": first.get("activite_principale"),
                        "categorie_entreprise": first.get("categorie_entreprise"),
                        "tranche_effectif": first.get("tranche_effectif_salarie"),
                        "etat_administratif": first.get("etat_administratif"),
                        "date_creation": first.get("date_creation"),
                        "siege_commune": siege.get("libelle_commune"),
                        "siege_code_postal": siege.get("code_postal"),
                        "est_association": complements.get("est_association", False),
                        "est_ess": complements.get("est_ess", False),
                        "est_finess": complements.get("est_finess", False),
                        "type_siae": complements.get("type_siae"),
                        "est_service_public": complements.get("est_service_public")
                    }
                else:
                    return {"found": False, "reason": "no_result"}
            elif r.status_code == 429:
                time.sleep(1.0 * (attempt + 1))
            else:
                time.sleep(0.3)
        except Exception as e:
            time.sleep(0.3)

    return {"found": False, "reason": "timeout_or_network"}


def select_target_sirens(df, max_sirens=None):
    """Sélectionne les SIRENs prioritaires à enrichir."""
    counts = df["SIREN_CLEAN"].value_counts()
    recurrent_sirens = set(counts[counts >= 2].index)

    has_social_flags = (
        (df["RES_PERS_AGEES"] == True) | (df["RES_PERS_AGEES"] == "true") |
        (df["RES_HANDICAPES"] == True) | (df["RES_HANDICAPES"] == "true") |
        (df["RES_SOCIALE"] == True) | (df["RES_SOCIALE"] == "true") |
        (df["NB_LGT_PRET_LOC_SOCIAL"] > 0) |
        (df["SURF_PUB_CREEE"] > 0) |
        (df["SURF_HEB_CREEE"] > 0)
    )

    is_social_ape = df["APE_DEM"].astype(str).str.startswith(("86.", "87.", "88.", "68.20A", "94."))
    is_social_cj = df["CJ_DEM"].isin([5202, 5546, 5547, 5548, 5550, 5515, 9220, 9210, 9230, 9300, 4140, 7210, 7300])
    kw_pattern = "EHPAD|HOPITAL|CLINIQUE|ASSOCIATION|FONDATION|FOYER|MEDIC|SOCIAL|HANDICAP|ENFANCE|SANTE|INSERTION|SOLIDAR|HABITAT|LOGEMENT"
    has_social_kw = df["DENOM_CLEAN"].astype(str).str.contains(kw_pattern, case=False, na=False)

    social_sirens = set(df[has_social_flags | is_social_ape | is_social_cj | has_social_kw]["SIREN_CLEAN"].dropna().unique())

    priority_set = recurrent_sirens.union(social_sirens)
    remaining_set = set(df["SIREN_CLEAN"].dropna().unique()) - priority_set

    ordered_priority = [s for s in counts.index if s in priority_set]
    ordered_remaining = [s for s in counts.index if s in remaining_set]

    all_ordered = ordered_priority + ordered_remaining

    if max_sirens is not None and max_sirens > 0:
        target = all_ordered[:max_sirens]
    else:
        target = all_ordered

    logger.info(f"SIRENs ciblés : {len(target)} ({len(ordered_priority)} prioritaires)")
    return target


def enrich_dataset(max_sirens=300, max_workers=2, offline_only=False):
    """
    Enrichit le jeu de données avec les métadonnées SIRENE (en cache ou via API).
    En cas d'indisponibilité du réseau / rate-limit, s'appuie sur le cache existant
    et les colonnes Sitadel sans bloquer le pipeline.
    """
    logger.info("Chargement des données Sitadel nettoyées (typage strict des SIREN)...")
    df = pd.read_csv(INPUT_CLEANED_PATH, sep=";", low_memory=False, dtype={"SIREN_CLEAN": str})

    # Assurer que SIREN_CLEAN est au format chaîne 9 chiffres
    df["SIREN_CLEAN"] = df["SIREN_CLEAN"].astype(str).str.replace(".0", "", regex=False).str.zfill(9)

    cache = load_cache()

    if not offline_only:
        target_sirens = select_target_sirens(df, max_sirens=max_sirens)
        sirens_to_query = [s for s in target_sirens if s not in cache]
        logger.info(f"SIRENs déjà en cache : {len(target_sirens) - len(sirens_to_query)} / {len(target_sirens)}")

        if sirens_to_query:
            logger.info(f"Requêtage API pour {len(sirens_to_query)} nouveaux SIRENs...")
            session = requests.Session()
            completed = 0
            t0 = time.time()

            try:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_siren = {executor.submit(query_api_siren, s, session): s for s in sirens_to_query}
                    for future in as_completed(future_to_siren):
                        s = future_to_siren[future]
                        try:
                            res = future.result()
                            cache[s] = res
                        except Exception as e:
                            cache[s] = {"found": False, "reason": str(e)}

                        completed += 1
                        if completed % 50 == 0 or completed == len(sirens_to_query):
                            save_cache(cache)
                            logger.info(f"Progression API : {completed}/{len(sirens_to_query)}")
            except Exception as e:
                logger.warning(f"Interruption requêtes API ({e}). Utilisation du cache accumulé.")

            save_cache(cache)

    # Fusion des enrichissements dans le DataFrame
    logger.info("Application des enrichissements SIRENE au jeu de données...")
    enrichment_records = []
    for siren in df["SIREN_CLEAN"]:
        siren_str = str(siren).strip()
        if siren_str in cache and cache[siren_str].get("found"):
            info = cache[siren_str]
            enrichment_records.append({
                "ENRICHI_SIRENE": True,
                "NOM_OFFICIEL_SIRENE": info.get("nom_officiel"),
                "CJ_SIRENE": info.get("cj_sirene"),
                "APE_SIRENE": info.get("ape_sirene"),
                "CATEGORIE_ENTREPRISE": info.get("categorie_entreprise"),
                "TRANCHE_EFFECTIF": info.get("tranche_effectif"),
                "ETAT_ADMIN_SIRENE": info.get("etat_administratif"),
                "SIEGE_COMMUNE": info.get("siege_commune"),
                "SIEGE_CP": info.get("siege_code_postal"),
                "EST_ASSOCIATION": info.get("est_association", False),
                "EST_ESS": info.get("est_ess", False),
                "EST_FINESS": info.get("est_finess", False),
                "TYPE_SIAE": info.get("type_siae")
            })
        else:
            enrichment_records.append({
                "ENRICHI_SIRENE": False,
                "NOM_OFFICIEL_SIRENE": None,
                "CJ_SIRENE": None,
                "APE_SIRENE": None,
                "CATEGORIE_ENTREPRISE": None,
                "TRANCHE_EFFECTIF": None,
                "ETAT_ADMIN_SIRENE": None,
                "SIEGE_COMMUNE": None,
                "SIEGE_CP": None,
                "EST_ASSOCIATION": False,
                "EST_ESS": False,
                "EST_FINESS": False,
                "TYPE_SIAE": None
            })

    df_enrich = pd.DataFrame(enrichment_records)
    for col in df_enrich.columns:
        df[col] = df_enrich[col]

    df.to_csv(ENRICHED_OUTPUT_PATH, index=False, sep=";")
    logger.info(f"Fichier enrichi exporté : {ENRICHED_OUTPUT_PATH} ({os.path.getsize(ENRICHED_OUTPUT_PATH) / 1e6:.2f} Mo)")

    # Statistiques d'enrichissement
    permis_enrichis = int(df["ENRICHI_SIRENE"].sum())
    stats = {
        "total_permis": len(df),
        "permis_enrichis": permis_enrichis,
        "taux_permis_enrichis": round(permis_enrichis / len(df), 4),
        "total_sirens_uniques": df["SIREN_CLEAN"].nunique(),
        "sirens_en_cache": len(cache),
        "sirens_trouves_api": sum(1 for s in cache.values() if s.get("found")),
        "permis_finess_identifies": int(df["EST_FINESS"].sum()),
        "permis_ess_identifies": int(df["EST_ESS"].sum()),
        "permis_associations_identifiees": int(df["EST_ASSOCIATION"].sum())
    }

    with open(STATS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    logger.info(f"Statistiques d'enrichissement sauvegardées dans : {STATS_OUTPUT_PATH}")

    return df, stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrichissement SIRENE pour permis 78")
    parser.add_argument("--limit", type=int, default=300, help="Nombre max de SIRENs à enrichir")
    parser.add_argument("--workers", type=int, default=2, help="Nombre de workers concurrents")
    parser.add_argument("--offline", action="store_true", help="Utiliser uniquement le cache existant")
    args = parser.parse_args()

    enrich_dataset(max_sirens=args.limit, max_workers=args.workers, offline_only=args.offline)
