#!/usr/bin/env python3
"""
scripts/run_pipeline.py
Buddimm - Cas d'étude Sitadel Yvelines (78)

Orchestrateur principal : exécute le pipeline complet de bout en bout
de manière 100% reproductible.

Étapes :
1. Ingestion et filtrage Sitadel 78 (personnes morales)
2. Enrichissement SIRENE / Annuaire des Entreprises (avec cache local)
3. Classification par familles d'acteurs et scoring de pertinence Buddimm
4. Analyses quantitatives, visualisations (outputs/*.png) et export CRM
"""

import os
import sys
import time
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("pipeline_runner")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

STEPS = [
    ("Étape 1 : Ingestion & Filtrage Sitadel 78", [sys.executable, os.path.join(SCRIPTS_DIR, "01_download_filter_sitadel.py")]),
    ("Étape 2 : Enrichissement SIRENE", [sys.executable, os.path.join(SCRIPTS_DIR, "02_enrich_sirene.py"), "--offline"]),
    ("Étape 3 : Classification Familles & Scoring", [sys.executable, os.path.join(SCRIPTS_DIR, "03_classify_families.py")]),
    ("Étape 4 : Analyses, Graphiques & Export CRM", [sys.executable, os.path.join(SCRIPTS_DIR, "04_analyze_patterns.py")]),
    ("Étape 5 : Audit Qualité & Conformité (20 cas)", [sys.executable, os.path.join(SCRIPTS_DIR, "05_audit_classification.py")]),
]


def run():
    logger.info("================================================================")
    logger.info("DÉMARRAGE DU PIPELINE COMPLET BUDDIMM - SITADEL 78")
    logger.info("================================================================")
    t_global = time.time()

    for step_name, cmd in STEPS:
        logger.info(f"\n>>> Lancement de : {step_name}")
        t_start = time.time()
        res = subprocess.run(cmd, cwd=BASE_DIR)
        if res.returncode != 0:
            logger.error(f"ÉCHEC lors de {step_name} (code sortie: {res.returncode})")
            sys.exit(res.returncode)
        logger.info(f">>> {step_name} terminé en {time.time() - t_start:.2f}s.")

    logger.info("\n================================================================")
    logger.info(f"PIPELINE EXÉCUTÉ AVEC SUCCÈS EN {time.time() - t_global:.2f}s.")
    logger.info("Tous les livrables sont disponibles dans le dossier outputs/")
    logger.info("================================================================")


if __name__ == "__main__":
    run()
