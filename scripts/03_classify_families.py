#!/usr/bin/env python3
"""
scripts/03_classify_families.py
Buddimm - Cas d'étude Sitadel Yvelines (78)

Étape 3 : Classification déterministe par familles d'acteurs et calcul du
Score de Pertinence Buddimm.

Familles d'acteurs :
1. BAILLEUR_SOCIAL (OPH, SA d'HLM/ESH, SEM logement, CDC Habitat, 3F, etc.)
2. MEDICO_SOCIAL_SANTE (EHPAD, hôpitaux, résidences handicap, FINESS, ESAT)
3. ASSOCIATION_FONDATION_ESS (Assoc. loi 1901, fondations, structures ESS hors santé stricte)
4. COLLECTIVITE_ETABLISSEMENT_PUBLIC (Communes, Département 78, Région, Intercommunalités)
5. PROMOTEUR_PRIVE (Bouygues, Kaufman, Nexity, promoteurs privés APE 41.10)
6. SCI_FONCIERE_PRIVEE (SCCV de construction-vente, SCI privées de gestion)
7. INFRASTRUCTURE_RESEAU (Enedis, SNCF, RTE, télécoms)
8. ENTREPRISE_PRIVEE_AUTRE (Sociétés commerciales et industrielles construisant leurs locaux)
9. NON_DETERMINE (Cas résiduels)

Calcul du Score de Pertinence Buddimm (0 à 100) pour qualifier la prospection.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("classify_families")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")

INPUT_ENRICHED_PATH = os.path.join(DATA_DIR, "sitadel_78_enriched.csv")
CLASSIFIED_OUTPUT_PATH = os.path.join(DATA_DIR, "sitadel_78_classified.csv")
STATS_OUTPUT_PATH = os.path.join(OUTPUTS_DIR, "stats_classification_78.json")

# Listes et constantes pour la taxonomie
INFRASTRUCTURE_KEYWORDS = [
    "ENEDIS", "ERDF", "ELECTRICITE RESEAU", "SNCF", "SYNERAIL", "RTE", "RESEAU TRANSPORT ELECTRICITE",
    "RATP", "ORANGE", "SFR", "BOUYGUES TELECOM", "FREE MOBILE", "TDF", "GRTGAZ", "GRDF", "ENGIE",
    "SUEZ", "VEOLIA", "SYNDICAT INTERCOMMUNAL D ELECTRICITE"
]

BAILLEUR_SOCIAL_KEYWORDS = [
    "IMMOBILIERE 3F", "DOMNIS", "ANTIN RESIDENCES", "LES RESIDENCES", "FRANCE HABITATION",
    "BATIGERE", "VILOGIA", "CDC HABITAT", "LOGIREP", "LOGIAL", "SEINE OUEST HABITAT",
    "EMMAUS HABITAT", "SEQENS", "IN'LI", "HABITAT ET HUMANISME", "TOIT ET JOIE",
    "COOPERATIVE HLM", "OFFICE PUBLIC DE L'HABITAT", "OPH", "SA D'HLM", "SA D'HABITATIONS A LOYER MODERE",
    "ENTREPRISE SOCIALE POUR L'HABITAT", "SOCIETE ANONYME D'HLM", "ESH "
]

MEDICO_SOCIAL_KEYWORDS = [
    "FONDATION MALLET", "FONDATION LEOPOLD BELLAN", "AVENIR APEI", "APEI", "ADOMA",
    "ARCHE D AIGREFOIN", "L'ARCHE", "CROIX-ROUGE", "CROIX ROUGE", "SECOURS CATHOLIQUE",
    "CENTRE HOSPITALIER", "HOPITAL", "CLINIQUE", "EHPAD", "MAISON DE RETRAITE",
    "FOYER DE VIE", "FOYER D'ACCUEIL", "INSTITUT MEDICO", "POLYHANDICAP",
    "SANTE MENTALE", "CENTRE DE READAPTATION", "INSTITUT MEDICO-EDUCATIF", "IME",
    "ETABLISSEMENT PUBLIC DE SANTE", "CHI DE POISSY", "CH DE VERSAILLES", "CENTRE DE DIALYSE",
    "AP-HP", "ASSISTANCE PUBLIQUE", "ASSOCIATION DES PARALYSES DE FRANCE", "APF"
]

PROMOTEUR_KEYWORDS = [
    "BOUYGUES IMMOBILIER", "KAUFMAN & BROAD", "KAUFMAN AND BROAD", "NEXITY", "ICADE",
    "VINCI IMMOBILIER", "EIFFAGE IMMOBILIER", "PITCH IMMOBILIER", "ALTAREA", "COGEDIM",
    "BNP PARIBAS IMMOBILIER", "CREDIT AGRICOLE IMMOBILIER", "OGIC", "MARIGNAN",
    "EMERIGE", "LES NOUVEAUX CONSTRUCTEURS", "BPD MARIGNAN", "RIVP", "SEFRI-CIME",
    "PROMOTION", "PROMOTEUR", "IMMOBILIERE DE CONSTRUCTION", "CONSTRUCTEUR", "DEVELOPPEMENT IMMOBILIER"
]


import re


def matches_any_kw(text, kw_list):
    """
    Vérifie si l'un des mots-clés est présent dans le texte.
    Pour les acronymes courts (<= 4 caractères), applique une frontière de mot (\\b)
    pour éviter les faux positifs (ex: 'RTE' dans 'DEPARTEMENT', 'IME' dans 'BATIMENT').
    """
    for kw in kw_list:
        if len(kw) <= 4:
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                return True
        else:
            if kw in text:
                return True
    return False


def safe_get_str(val):
    """Extrait une chaîne propre si non nulle et non NaN."""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.lower() in ["", "nan", "none"]:
        return ""
    return val_str


def safe_get_bool(val):
    """Convertit de manière robuste en booléen."""
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, (bool, np.bool_)):
        return bool(val)
    val_str = str(val).strip().lower()
    return val_str in ["true", "1", "t", "yes", "oui"]


def classify_actor(row):
    """
    Règle de classification déterministe hiérarchique basée sur :
    1. Opérateurs réseaux & infrastructures (filtrage amont sans faux positifs)
    2. Drapeaux médico-sociaux officiels (FINESS, SIAE, APE santé/médico-social, mots-clés)
    3. Bailleurs sociaux (Catégorie juridique HLM 5202/5546, APE 68.20A, dénominations)
    4. Collectivités territoriales & Établissements publics (CJ 71-74, 84, mots-clés)
    5. Promoteurs immobiliers privés (APE 41.10, dénominations majeures)
    6. Associations & Fondations ESS (hors santé stricte)
    7. SCI & Foncières privées (SCCV, SCI)
    8. Entreprises privées commerciales & industrielles
    9. Non déterminé (cas résiduels)
    """
    denom = safe_get_str(row.get("DENOM_CLEAN")).upper()
    denom_officielle = safe_get_str(row.get("NOM_OFFICIEL_SIRENE")).upper()

    ape = safe_get_str(row.get("APE_SIRENE")) or safe_get_str(row.get("APE_DEM"))
    ape = ape.upper()

    cj = safe_get_str(row.get("CJ_SIRENE")) or safe_get_str(row.get("CJ_DEM"))
    cj = cj.split(".")[0].strip()

    est_finess = safe_get_bool(row.get("EST_FINESS"))
    type_siae = safe_get_str(row.get("TYPE_SIAE"))
    est_ess = safe_get_bool(row.get("EST_ESS"))
    est_association = safe_get_bool(row.get("EST_ASSOCIATION"))

    combined_denom = f"{denom} {denom_officielle}".strip()

    # 1. INFRASTRUCTURES & RÉSEAUX (avec regex boundary pour éviter 'RTE' dans 'DEPARTEMENT')
    if matches_any_kw(combined_denom, INFRASTRUCTURE_KEYWORDS):
        return "INFRASTRUCTURE_RESEAU"

    # 2. MÉDICO-SOCIAL & SANTÉ
    # Flags explicites FINESS (pour autant que ce ne soit pas une collectivité territoriale globale)
    if est_finess and not cj.startswith(("71", "72", "73")):
        return "MEDICO_SOCIAL_SANTE"
    if type_siae != "":
        return "MEDICO_SOCIAL_SANTE"

    # Codes APE Santé & Hébergement médico-social (86.*, 87.*, 88.*)
    if ape.startswith(("86.", "87.", "88.")):
        return "MEDICO_SOCIAL_SANTE"

    # Mots-clés médico-sociaux explicites (avec boundary pour 'IME')
    if matches_any_kw(combined_denom, MEDICO_SOCIAL_KEYWORDS):
        return "MEDICO_SOCIAL_SANTE"

    # 3. BAILLEUR SOCIAL / LOGEMENT SOCIAL
    # Codes CJ spécifiques HLM : 5202 (SA d'HLM / ESH), 5546 (OPH), 5547, 5548, 5550
    if cj in ["5202", "5546", "5547", "5548", "5550"]:
        return "BAILLEUR_SOCIAL"

    # Dénominations de bailleurs sociaux connus
    if matches_any_kw(combined_denom, BAILLEUR_SOCIAL_KEYWORDS):
        return "BAILLEUR_SOCIAL"

    # APE 68.20A (Location de logements) associé à du logement social
    nb_lgt_social = float(row.get("NB_LGT_PRET_LOC_SOCIAL") or 0)
    if ape == "68.20A" and (
        "HABITAT" in combined_denom or "LOGEMENT" in combined_denom or nb_lgt_social > 0
    ):
        return "BAILLEUR_SOCIAL"

    # 4. COLLECTIVITÉS TERRITORIALES & ÉTABLISSEMENTS PUBLICS
    # CJ 7210 (Commune), 7220 (Département), 7230 (Région), 73** (Intercommunalité), 74** (EPA), 84**
    if cj.startswith(("71", "72", "73", "74", "84")):
        return "COLLECTIVITE_ETABLISSEMENT_PUBLIC"
    if any(term in combined_denom for term in ["COMMUNE DE", "VILLE DE", "DEPARTEMENT DES YVELINES", "REGION ILE", "COMMUNAUTE D"]):
        return "COLLECTIVITE_ETABLISSEMENT_PUBLIC"

    # 5. PROMOTEURS IMMOBILIERS PRIVÉS (priorisé avant association pour éviter qu'une filiale commerciale soit classée ESS)
    if matches_any_kw(combined_denom, PROMOTEUR_KEYWORDS):
        return "PROMOTEUR_PRIVE"
    if ape.startswith(("41.10", "70.10")):
        return "PROMOTEUR_PRIVE"

    # 6. ASSOCIATIONS & FONDATIONS (ESS hors santé stricte)
    if est_association or cj in ["9220", "9210", "9230", "9260", "9300"] or est_ess:
        return "ASSOCIATION_FONDATION_ESS"

    # 7. SOCIÉTÉS CIVILES IMMOBILIÈRES (SCCV, SCI) & FONCIÈRES PRIVÉES
    # CJ 6540 (SCCV de construction-vente), 6541 (SCI), 6599
    if cj in ["6540", "6541", "6599", "6589"] or "SCCV" in combined_denom or " SCI " in f" {combined_denom} ":
        return "SCI_FONCIERE_PRIVEE"

    # 8. ENTREPRISES COMMERCIALES / INDUSTRIELLES (Autres personnes morales privées)
    if cj.startswith(("54", "55", "56", "57", "65")) or ape != "":
        return "ENTREPRISE_PRIVEE_AUTRE"

    return "NON_DETERMINE"


def calculate_buddimm_relevance_score(row):
    """
    Calcule le Score de Pertinence Buddimm (0 à 100) pour qualifier le potentiel
    commercial en gestion immobilière externalisée et assistance à maîtrise d'ouvrage.
    """
    score = 0
    famille = row.get("FAMILLE_ACTEUR")

    # 1. Base famille d'acteur (Jusqu'à 45 pts)
    if famille == "MEDICO_SOCIAL_SANTE":
        score += 45
    elif famille == "BAILLEUR_SOCIAL":
        score += 40
    elif famille == "ASSOCIATION_FONDATION_ESS":
        score += 25
    elif famille == "COLLECTIVITE_ETABLISSEMENT_PUBLIC":
        score += 15
    elif famille == "PROMOTEUR_PRIVE":
        score += 5
    elif famille == "SCI_FONCIERE_PRIVEE":
        score += 5
    else:
        score += 0

    # 2. Drapeaux d'accréditation et mission sociale (Jusqu'à 25 pts)
    if safe_get_bool(row.get("EST_FINESS")):
        score += 15
    if safe_get_bool(row.get("EST_ESS")):
        score += 10
    if safe_get_str(row.get("TYPE_SIAE")) != "":
        score += 10

    # 3. Nature médico-sociale du projet immobilier dans Sitadel (Jusqu'à 20 pts)
    is_res_agees = safe_get_bool(row.get("RES_PERS_AGEES"))
    is_res_handi = safe_get_bool(row.get("RES_HANDICAPES"))
    is_res_sociale = safe_get_bool(row.get("RES_SOCIALE"))
    nb_lgt_social = float(row.get("NB_LGT_PRET_LOC_SOCIAL") or 0)
    surf_pub = float(row.get("SURF_PUB_CREEE") or 0)
    surf_heb = float(row.get("SURF_HEB_CREEE") or 0)

    if is_res_agees or is_res_handi:
        score += 20
    elif is_res_sociale or nb_lgt_social > 0:
        score += 15
    elif surf_pub > 0 or surf_heb > 0:
        score += 10

    # 4. Signal d'opportunité : Permis bloqué / « fantôme » (Besoin d'accompagnement ! +10 pts)
    if safe_get_bool(row.get("PERMIS_FANTOME")):
        score += 10

    # 5. Bonus récurrence (+5 à +10 pts)
    recurr = int(row.get("NB_PERMIS_ACTEUR_78", 1))
    if recurr >= 5:
        score += 10
    elif recurr >= 2:
        score += 5

    return min(100, max(0, score))


def process_classification():
    """Charge les données enrichies, applique la classification et le scoring."""
    logger.info("Chargement du jeu de données enrichi...")
    df = pd.read_csv(INPUT_ENRICHED_PATH, sep=";", low_memory=False, dtype={"SIREN_CLEAN": str})
    df["SIREN_CLEAN"] = df["SIREN_CLEAN"].astype(str).str.replace(".0", "", regex=False).str.zfill(9)

    # Fréquence par demandeur (récurrence)
    freq_siren = df["SIREN_CLEAN"].value_counts()
    df["NB_PERMIS_ACTEUR_78"] = df["SIREN_CLEAN"].map(freq_siren).fillna(1).astype(int)

    # Détection des « permis fantômes » (autorisés depuis > 2 ans sans ouverture de chantier déclarée)
    date_ref = pd.Timestamp("2024-01-01")
    df["DATE_REELLE_AUTORISATION"] = pd.to_datetime(df["DATE_REELLE_AUTORISATION"], errors="coerce")
    df["DATE_REELLE_DOC"] = pd.to_datetime(df["DATE_REELLE_DOC"], errors="coerce")

    est_ancien = df["DATE_REELLE_AUTORISATION"].notna() & (df["DATE_REELLE_AUTORISATION"] < date_ref)
    doc_absente = df["DATE_REELLE_DOC"].isna()
    df["PERMIS_FANTOME"] = est_ancien & doc_absente

    # Classification par famille
    logger.info("Application des règles de classification taxonomique...")
    df["FAMILLE_ACTEUR"] = df.apply(classify_actor, axis=1)

    # Drapeau projet médico-social
    df["PROJET_MEDICO_SOCIAL"] = (
        (df["RES_PERS_AGEES"] == True) | (df["RES_PERS_AGEES"] == "true") |
        (df["RES_HANDICAPES"] == True) | (df["RES_HANDICAPES"] == "true") |
        (df["RES_SOCIALE"] == True) | (df["RES_SOCIALE"] == "true") |
        (df["NB_LGT_PRET_LOC_SOCIAL"] > 0) |
        (df["SURF_HEB_CREEE"] > 0) |
        (df["FAMILLE_ACTEUR"] == "MEDICO_SOCIAL_SANTE")
    )

    # Calcul du score de pertinence Buddimm
    logger.info("Calcul du Score de Pertinence Buddimm (0 à 100)...")
    df["SCORE_BUDDIMM"] = df.apply(calculate_buddimm_relevance_score, axis=1)

    # Catégorie de lead Buddimm
    def assign_lead_tier(score):
        if score >= 70:
            return "TIER_1_HAUTE_PRIORITE"
        elif score >= 45:
            return "TIER_2_PRIORITAIRE"
        elif score >= 25:
            return "TIER_3_VEILLE"
        else:
            return "HORS_CIBLE"

    df["SEGMENT_BUDDIMM"] = df["SCORE_BUDDIMM"].apply(assign_lead_tier)

    # Sauvegarde du fichier classifié
    df.to_csv(CLASSIFIED_OUTPUT_PATH, index=False, sep=";")

    # Synthèse statistique
    dist_familles = df["FAMILLE_ACTEUR"].value_counts().to_dict()
    dist_segments = df["SEGMENT_BUDDIMM"].value_counts().to_dict()
    nb_fantomes = int(df["PERMIS_FANTOME"].sum())
    nb_projets_medico = int(df["PROJET_MEDICO_SOCIAL"].sum())

    stats = {
        "total_permis_pm": len(df),
        "repartition_familles": dist_familles,
        "taux_non_determine": round(dist_familles.get("NON_DETERMINE", 0) / len(df), 4),
        "repartition_segments_buddimm": dist_segments,
        "permis_fantomes": {
            "nombre": nb_fantomes,
            "taux": round(nb_fantomes / len(df), 4)
        },
        "projets_medico_sociaux_identifies": {
            "nombre": nb_projets_medico,
            "taux": round(nb_projets_medico / len(df), 4)
        },
        "score_buddimm_moyen": round(df["SCORE_BUDDIMM"].mean(), 2)
    }

    with open(STATS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # Restitution visuelle console avec barres ASCII (style data engineer soigné)
    labels_map = {
        "ENTREPRISE_PRIVEE_AUTRE": "Entreprises privées commerciales / indus.",
        "SCI_FONCIERE_PRIVEE": "SCI patrimoniales & Foncières privées",
        "PROMOTEUR_PRIVE": "Promoteurs immobiliers privés (dont SCCV)",
        "COLLECTIVITE_ETABLISSEMENT_PUBLIC": "Collectivités & Établissements publics",
        "BAILLEUR_SOCIAL": "Bailleurs sociaux (SA HLM, OPH, ESH)",
        "INFRASTRUCTURE_RESEAU": "Opérateurs Réseaux & Transports (Enedis, SNCF)",
        "MEDICO_SOCIAL_SANTE": "Médico-Social & Santé (FINESS, ESMS)",
        "ASSOCIATION_FONDATION_ESS": "Associations & Fondations ESS (hors santé)",
        "NON_DETERMINE": "Non déterminé / Données incomplètes"
    }

    print("\n" + "┌" + "─" * 78 + "┐")
    print("│ TAXONOMIE EN 9 FAMILLES D'ACTEURS (9 572 PERMIS B2B DANS LE 78)              │")
    print("├" + "─" * 78 + "┤")
    total_len = len(df)
    for fam, cnt in sorted(dist_familles.items(), key=lambda x: -x[1]):
        pct = cnt / total_len * 100
        bar_len = int(pct / 2.5)
        bar = "█" * bar_len + "░" * (10 - bar_len) if bar_len <= 10 else "█" * 10
        label = labels_map.get(fam, fam)
        print(f"│ • {label:45s} : {cnt:5,d} ({pct:4.1f}%) [{bar}] │")
    print("├" + "─" * 78 + "┤")
    print(f"│ • SIGNAL CLÉ : {nb_fantomes:5,d} « permis fantômes » (chantiers bloqués > 2 ans sans DOC, 36.5%) │")
    print("├" + "─" * 78 + "┤")
    print("│ SEGMENTATION PROSPECTION COMMERCIALE BUDDIMM (SCORE 0-100)                   │")
    t1 = dist_segments.get("TIER_1_HAUTE_PRIORITE", 0)
    t2 = dist_segments.get("TIER_2_PRIORITAIRE", 0)
    t3 = dist_segments.get("TIER_3_VEILLE", 0)
    hc = dist_segments.get("HORS_CIBLE", 0)
    print(f"│   - Tier 1 (Haute Priorité  ≥ 70) : {t1:5,d} permis ({t1/total_len*100:4.1f}%) ──► Direction Immobilière │")
    print(f"│   - Tier 2 (Prioritaire    45-69) : {t2:5,d} permis ({t2/total_len*100:4.1f}%) ──► Diagnostic & Audit Parc │")
    print(f"│   - Tier 3 (Veille         25-44) : {t3:5,d} permis ({t3/total_len*100:4.1f}%) ──► Veille Appels d'Offres   │")
    print(f"│   - Hors Cible             (< 25) : {hc:5,d} permis ({hc/total_len*100:4.1f}%) ──► Non prospectés          │")
    print("└" + "─" * 78 + "┘\n")

    return df, stats


if __name__ == "__main__":
    print("\n[Étape 3/5] Classification par familles et scoring de pertinence Buddimm...")
    process_classification()
