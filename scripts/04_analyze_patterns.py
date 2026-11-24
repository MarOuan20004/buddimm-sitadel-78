#!/usr/bin/env python3
"""
scripts/04_analyze_patterns.py
Buddimm - Cas d'étude Sitadel Yvelines (78)

Étape 4 : Analyses quantitatives, génération des graphiques décisionnels (outputs/*.png),
synthèse métier chiffrée et export CRM des prospects qualifiés pour Buddimm.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("analyze_patterns")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")

INPUT_CLASSIFIED_PATH = os.path.join(DATA_DIR, "sitadel_78_classified.csv")
CRM_EXPORT_PATH = os.path.join(OUTPUTS_DIR, "crm_export_prospects_buddimm.csv")
SYNTHESE_METIER_PATH = os.path.join(OUTPUTS_DIR, "synthese_metier_buddimm.json")

# Palette visuelle soignée (Modern Data Analytics Palette)
PALETTE = {
    "BAILLEUR_SOCIAL": "#1f77b4",             # Bleu institutionnel
    "MEDICO_SOCIAL_SANTE": "#e377c2",         # Rose vif / santé
    "ASSOCIATION_FONDATION_ESS": "#9467bd",   # Violet solidaire
    "COLLECTIVITE_ETABLISSEMENT_PUBLIC": "#2ca02c", # Vert public
    "PROMOTEUR_PRIVE": "#ff7f0e",             # Orange commercial
    "SCI_FONCIERE_PRIVEE": "#8c564b",         # Brun foncier
    "INFRASTRUCTURE_RESEAU": "#7f7f7f",       # Gris réseau
    "ENTREPRISE_PRIVEE_AUTRE": "#bcbd22",     # Jaune/vert entreprise
    "NON_DETERMINE": "#d62728",               # Rouge ambiguïté
    "TIER_1": "#d62728",                      # Rouge alerte / top priorité
    "TIER_2": "#ff7f0e",                      # Orange priorité
    "TIER_3": "#2ca02c",                      # Vert veille
    "HORS_CIBLE": "#7f7f7f"                   # Gris neutre
}

LABELS_FAMILLES_FR = {
    "BAILLEUR_SOCIAL": "Bailleurs sociaux (OPH, ESH, HLM)",
    "MEDICO_SOCIAL_SANTE": "Médico-social & Santé (ESMS, FINESS)",
    "ASSOCIATION_FONDATION_ESS": "Associations & Fondations ESS",
    "COLLECTIVITE_ETABLISSEMENT_PUBLIC": "Collectivités & Établissements publics",
    "PROMOTEUR_PRIVE": "Promoteurs immobiliers privés",
    "SCI_FONCIERE_PRIVEE": "SCI & Foncières privées (SCCV)",
    "INFRASTRUCTURE_RESEAU": "Opérateurs Réseaux & Transports",
    "ENTREPRISE_PRIVEE_AUTRE": "Autres entreprises privées",
    "NON_DETERMINE": "Non déterminé / Cas résiduels"
}


def setup_matplotlib():
    """Configure les paramètres globaux de Matplotlib pour des visualisations premium."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["grid.color"] = "#e5e5e5"
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["grid.alpha"] = 0.7


def plot_01_distribution_familles(df):
    """Figure 1 : Distribution des permis et volumes par famille d'acteur."""
    logger.info("Génération de Figure 1 : Distribution des familles...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=300)

    fam_counts = df["FAMILLE_ACTEUR"].value_counts()
    fam_labels = [LABELS_FAMILLES_FR.get(f, f) for f in fam_counts.index]
    colors = [PALETTE.get(f, "#333333") for f in fam_counts.index]

    # Subplot 1 : Nombre de permis
    bars1 = ax1.barh(range(len(fam_counts)), fam_counts.values, color=colors, height=0.65, edgecolor="none")
    ax1.set_yticks(range(len(fam_counts)))
    ax1.set_yticklabels(fam_labels, fontsize=10)
    ax1.invert_yaxis()
    ax1.set_xlabel("Nombre d'autorisations d'urbanisme (2013-2026)", fontsize=11, fontweight="bold", labelpad=10)
    ax1.set_title("Volume de permis par famille d'acteurs", fontsize=13, fontweight="bold", pad=12)
    ax1.grid(True, axis="x")

    for bar in bars1:
        w = bar.get_width()
        pct = w / len(df) * 100
        ax1.text(w + 40, bar.get_y() + bar.get_height() / 2, f"{int(w):,d} ({pct:.1f}%)",
                 va="center", ha="left", fontsize=9, fontweight="bold", color="#333333")

    # Subplot 2 : Surfaces créées estimées (m²)
    # Somme des surfaces habitables créées et surfaces locaux créées
    df["SURF_TOTALE_ESTIMEE"] = df["SURF_HAB_CREEE"].fillna(0) + df["SURF_LOC_CREEE"].fillna(0)
    surf_by_fam = df.groupby("FAMILLE_ACTEUR")["SURF_TOTALE_ESTIMEE"].sum().loc[fam_counts.index] / 1000  # en milliers de m²

    bars2 = ax2.barh(range(len(surf_by_fam)), surf_by_fam.values, color=colors, height=0.65, edgecolor="none")
    ax2.set_yticks(range(len(surf_by_fam)))
    ax2.set_yticklabels([])
    ax2.invert_yaxis()
    ax2.set_xlabel("Surface totale créée (en milliers de m² de plancher)", fontsize=11, fontweight="bold", labelpad=10)
    ax2.set_title("Effort de construction (milliers de m² créés)", fontsize=13, fontweight="bold", pad=12)
    ax2.grid(True, axis="x")

    for bar in bars2:
        w = bar.get_width()
        pct = w / surf_by_fam.sum() * 100 if surf_by_fam.sum() > 0 else 0
        ax2.text(w + 15, bar.get_y() + bar.get_height() / 2, f"{int(w):,d}k m² ({pct:.1f}%)",
                 va="center", ha="left", fontsize=9, fontweight="bold", color="#333333")

    fig.suptitle("Écosystème de la construction dans les Yvelines (78) — Cartographie des Personnes Morales",
                 fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    out_path = os.path.join(OUTPUTS_DIR, "01_distribution_familles.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Figure 1 sauvegardée : {out_path}")


def plot_02_top_acteurs_medicosocial_social(df):
    """Figure 2 : Palmarès des acteurs médico-sociaux, fondations et bailleurs sociaux."""
    logger.info("Génération de Figure 2 : Top acteurs médico-sociaux & sociaux...")
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)

    # Filtrer les acteurs cibles Buddimm (Médico-social, Bailleurs sociaux, ESS)
    cibles = df[df["FAMILLE_ACTEUR"].isin(["MEDICO_SOCIAL_SANTE", "BAILLEUR_SOCIAL", "ASSOCIATION_FONDATION_ESS"])]
    top_acteurs = cibles.groupby(["DENOM_CLEAN", "FAMILLE_ACTEUR"]).agg(
        nb_permis=("NUM_DAU", "count"),
        surf_totale=("SURF_TOTALE_ESTIMEE", "sum"),
        nb_fantomes=("PERMIS_FANTOME", "sum")
    ).reset_index().sort_values("nb_permis", ascending=False).head(20)

    colors = [PALETTE.get(f, "#1f77b4") for f in top_acteurs["FAMILLE_ACTEUR"]]

    bars = ax.barh(range(len(top_acteurs)), top_acteurs["nb_permis"], color=colors, height=0.68)
    ax.set_yticks(range(len(top_acteurs)))
    ax.set_yticklabels(top_acteurs["DENOM_CLEAN"], fontsize=10, fontweight="medium")
    ax.invert_yaxis()
    ax.set_xlabel("Nombre de permis déposés dans le 78 (2013-2026)", fontsize=11, fontweight="bold", labelpad=10)
    ax.set_title("Top 20 des acteurs Médico-Sociaux, Fondations & Bailleurs Sociaux dans les Yvelines\n"
                 "(Cibles directes pour l'offre de gestion immobilière et AMO Buddimm)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.grid(True, axis="x")

    for i, (_, row) in enumerate(top_acteurs.iterrows()):
        nb = int(row["nb_permis"])
        fam_label = "Médico-social" if row["FAMILLE_ACTEUR"] == "MEDICO_SOCIAL_SANTE" else ("Bailleur HLM" if row["FAMILLE_ACTEUR"] == "BAILLEUR_SOCIAL" else "Fondation/ESS")
        fant = int(row["nb_fantomes"])
        annot = f"{nb} permis [{fam_label}]"
        if fant > 0:
            annot += f" • {fant} non démarré(s)"
        ax.text(nb + 0.5, i, annot, va="center", ha="left", fontsize=9, fontweight="bold", color="#222222")

    # Légende manuelle personnalisée
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=PALETTE["MEDICO_SOCIAL_SANTE"], label="Médico-Social & Santé (Fondations, ESMS)"),
        Patch(facecolor=PALETTE["BAILLEUR_SOCIAL"], label="Bailleurs Sociaux (OPH, ESH, HLM)"),
        Patch(facecolor=PALETTE["ASSOCIATION_FONDATION_ESS"], label="Associations & Fondations ESS")
    ]
    ax.legend(handles=legend_elements, loc="lower right", frameon=True, fontsize=10)

    plt.tight_layout()
    out_path = os.path.join(OUTPUTS_DIR, "02_top_acteurs_medicosocial_social.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Figure 2 sauvegardée : {out_path}")


def plot_03_dynamique_temporelle(df):
    """Figure 3 : Évolution annuelle des dépôts de permis par famille."""
    logger.info("Génération de Figure 3 : Dynamique temporelle...")
    fig, ax = plt.subplots(figsize=(14, 6.5), dpi=300)

    # Filtrer les années complètes (2013 à 2025)
    df_temp = df[(df["ANNEE_AUTORISATION"] >= 2013) & (df["ANNEE_AUTORISATION"] <= 2025)]
    ct = pd.crosstab(df_temp["ANNEE_AUTORISATION"].astype(int), df_temp["FAMILLE_ACTEUR"])

    top_familles_plot = [
        "PROMOTEUR_PRIVE", "BAILLEUR_SOCIAL", "MEDICO_SOCIAL_SANTE",
        "COLLECTIVITE_ETABLISSEMENT_PUBLIC", "SCI_FONCIERE_PRIVEE"
    ]

    for fam in top_familles_plot:
        if fam in ct.columns:
            series = ct[fam]
            ax.plot(series.index, series.values, marker="o", linewidth=2.5,
                    markersize=6, label=LABELS_FAMILLES_FR.get(fam, fam),
                    color=PALETTE.get(fam, "#333333"))

    ax.set_title("Évolution des dépôts d'autorisations d'urbanisme dans le 78 par famille (2013-2025)\n"
                 "Mise en évidence de la résilience du secteur Médico-Social face aux cycles économiques",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Année d'autorisation", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_ylabel("Nombre de permis autorisés", fontsize=11, fontweight="bold", labelpad=8)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.grid(True)
    ax.legend(loc="upper right", frameon=True, fontsize=9.5)

    # Annoter les événements clés
    ax.axvspan(2019.8, 2020.8, color="#fee08b", alpha=0.3, label="Choc sanitaire COVID-19")
    ax.text(2020.3, ax.get_ylim()[1] * 0.88, "Crise COVID-19\n(gel des dépôts)",
            ha="center", fontsize=8.5, style="italic", color="#8c510a")

    ax.axvspan(2022.5, 2024.5, color="#f4a582", alpha=0.25)
    ax.text(2023.5, ax.get_ylim()[1] * 0.78, "Crise immobilière\n(taux + coûts BTP)",
            ha="center", fontsize=8.5, style="italic", color="#b2182b")

    plt.tight_layout()
    out_path = os.path.join(OUTPUTS_DIR, "03_dynamique_temporelle.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Figure 3 sauvegardée : {out_path}")


def plot_04_top_communes_78(df):
    """Figure 4 : Concentration géographique communale du médico-social et du logement social."""
    logger.info("Génération de Figure 4 : Concentration géographique communale...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=300)

    # Récupérer le code postal ou la commune (ADR_LOCALITE_TER ou COMM)
    df["COMMUNE_LIBELLE"] = df["LOCALITE_DEM"].fillna(df["COMM"]).astype(str).str.upper()

    # Filtre médico-social
    df_medico = df[df["FAMILLE_ACTEUR"] == "MEDICO_SOCIAL_SANTE"]
    top_com_medico = df_medico["COMMUNE_LIBELLE"].value_counts().head(12)

    # Filtre bailleurs sociaux
    df_social = df[df["FAMILLE_ACTEUR"] == "BAILLEUR_SOCIAL"]
    top_com_social = df_social["COMMUNE_LIBELLE"].value_counts().head(12)

    ax1.barh(range(len(top_com_medico)), top_com_medico.values, color=PALETTE["MEDICO_SOCIAL_SANTE"], height=0.65)
    ax1.set_yticks(range(len(top_com_medico)))
    ax1.set_yticklabels(top_com_medico.index, fontsize=10)
    ax1.invert_yaxis()
    ax1.set_xlabel("Nombre de permis Médico-Social & Santé", fontsize=11, fontweight="bold")
    ax1.set_title("Top communes 78 : Projets Médico-Sociaux & Santé\n(Pôles hospitaliers, EHPAD, ESMS)",
                  fontsize=12, fontweight="bold", pad=10)
    ax1.grid(True, axis="x")

    for i, v in enumerate(top_com_medico.values):
        ax1.text(v + 0.3, i, str(v), va="center", ha="left", fontweight="bold", fontsize=9.5)

    ax2.barh(range(len(top_com_social)), top_com_social.values, color=PALETTE["BAILLEUR_SOCIAL"], height=0.65)
    ax2.set_yticks(range(len(top_com_social)))
    ax2.set_yticklabels(top_com_social.index, fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel("Nombre de permis Bailleurs Sociaux", fontsize=11, fontweight="bold")
    ax2.set_title("Top communes 78 : Logements Sociaux\n(Programmes HLM, rénovations urbaines ANRU)",
                  fontsize=12, fontweight="bold", pad=10)
    ax2.grid(True, axis="x")

    for i, v in enumerate(top_com_social.values):
        ax2.text(v + 0.5, i, str(v), va="center", ha="left", fontweight="bold", fontsize=9.5)

    fig.suptitle("Analyse Territoriale des Yvelines — Bassins d'activité prioritaires",
                 fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    out_path = os.path.join(OUTPUTS_DIR, "04_top_communes_78.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Figure 4 sauvegardée : {out_path}")


def plot_05_permis_fantomes_analyse(df):
    """Figure 5 : Analyse des permis fantômes (autorisés > 2 ans sans ouverture de chantier déclarée)."""
    logger.info("Génération de Figure 5 : Permis fantômes...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5), dpi=300)

    # Taux de permis fantômes par famille
    stats_fant = df.groupby("FAMILLE_ACTEUR").agg(
        total=("NUM_DAU", "count"),
        fantomes=("PERMIS_FANTOME", "sum")
    )
    stats_fant["taux_fantome_pct"] = stats_fant["fantomes"] / stats_fant["total"] * 100
    stats_fant = stats_fant[stats_fant["total"] >= 50].sort_values("taux_fantome_pct", ascending=True)

    labels = [LABELS_FAMILLES_FR.get(f, f) for f in stats_fant.index]
    colors = ["#e41a1c" if f in ["MEDICO_SOCIAL_SANTE", "BAILLEUR_SOCIAL"] else "#4daf4a" for f in stats_fant.index]

    bars = ax1.barh(range(len(stats_fant)), stats_fant["taux_fantome_pct"], color=colors, height=0.65)
    ax1.set_yticks(range(len(stats_fant)))
    ax1.set_yticklabels(labels, fontsize=9.5)
    ax1.set_xlabel("Taux de permis non démarrés après 2 ans (%)", fontsize=11, fontweight="bold")
    ax1.set_title("Taux de permis « fantômes » par famille d'acteur\n(Signal de risque d'abandon ou de blocage financier/technique)",
                  fontsize=12, fontweight="bold", pad=10)
    ax1.grid(True, axis="x")

    for bar, (_, row) in zip(bars, stats_fant.iterrows()):
        w = bar.get_width()
        cnt = int(row["fantomes"])
        tot = int(row["total"])
        ax1.text(w + 0.5, bar.get_y() + bar.get_height() / 2, f"{w:.1f}% ({cnt}/{tot})",
                 va="center", ha="left", fontsize=9, fontweight="bold")

    # Zoom sur les acteurs médico-sociaux et bailleurs sociaux avec des permis bloqués
    bloques_cibles = df[
        df["FAMILLE_ACTEUR"].isin(["MEDICO_SOCIAL_SANTE", "BAILLEUR_SOCIAL"]) &
        df["PERMIS_FANTOME"]
    ]["DENOM_CLEAN"].value_counts().head(10)

    ax2.barh(range(len(bloques_cibles)), bloques_cibles.values, color="#e41a1c", height=0.65)
    ax2.set_yticks(range(len(bloques_cibles)))
    ax2.set_yticklabels(bloques_cibles.index, fontsize=9.5, fontweight="medium")
    ax2.invert_yaxis()
    ax2.set_xlabel("Nombre de permis bloqués / non démarrés", fontsize=11, fontweight="bold")
    ax2.set_title("Organisations prioritaires avec chantiers en souffrance\n(Opportunités immédiates d'Assistance à Maîtrise d'Ouvrage)",
                  fontsize=12, fontweight="bold", pad=10)
    ax2.grid(True, axis="x")

    for i, v in enumerate(bloques_cibles.values):
        ax2.text(v + 0.2, i, f"{v} projet(s)", va="center", ha="left", fontweight="bold", fontsize=9.5)

    plt.tight_layout()
    out_path = os.path.join(OUTPUTS_DIR, "05_permis_fantomes_analyse.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Figure 5 sauvegardée : {out_path}")


def plot_06_scoring_buddimm_matrice(df):
    """Figure 6 : Matrice de segmentation et distribution des scores de pertinence Buddimm."""
    logger.info("Génération de Figure 6 : Matrice de scoring Buddimm...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=300)

    # Répartition par segment
    seg_counts = df["SEGMENT_BUDDIMM"].value_counts().reindex([
        "TIER_1_HAUTE_PRIORITE", "TIER_2_PRIORITAIRE", "TIER_3_VEILLE", "HORS_CIBLE"
    ]).fillna(0)

    seg_colors = [PALETTE["TIER_1"], PALETTE["TIER_2"], PALETTE["TIER_3"], PALETTE["HORS_CIBLE"]]
    seg_labels = [
        "Tier 1 : Haute priorité (Score ≥ 70)\nActeurs médico-sociaux & HLM récurrents",
        "Tier 2 : Prioritaire (Score 45-69)\nAssociations ESS & bailleurs ponctuels",
        "Tier 3 : Veille stratégique (Score 25-44)\nCollectivités & promoteurs avec mixité",
        "Hors cible (Score < 25)\nInfrastructures, commerces, SCI privées"
    ]

    bars = ax1.bar(range(len(seg_counts)), seg_counts.values, color=seg_colors, width=0.6, edgecolor="#333333", linewidth=0.8)
    ax1.set_xticks(range(len(seg_counts)))
    ax1.set_xticklabels(["Tier 1\n(≥70)", "Tier 2\n(45-69)", "Tier 3\n(25-44)", "Hors Cible\n(<25)"], fontsize=10, fontweight="bold")
    ax1.set_ylabel("Nombre de permis d'urbanisme", fontsize=11, fontweight="bold")
    ax1.set_title("Segmentation commerciale du portefeuille d'autorisations 78\n(Score de Pertinence Buddimm)",
                  fontsize=12, fontweight="bold", pad=12)
    ax1.grid(True, axis="y")

    for bar in bars:
        h = bar.get_height()
        pct = h / len(df) * 100
        ax1.text(bar.get_x() + bar.get_width() / 2, h + 80, f"{int(h):,d}\n({pct:.1f}%)",
                 ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    # Scatter plot Acteurs : Récurrence vs Score Buddimm
    acteurs_agg = df.groupby(["SIREN_CLEAN", "DENOM_CLEAN", "FAMILLE_ACTEUR"]).agg(
        nb_permis=("NUM_DAU", "count"),
        score_max=("SCORE_BUDDIMM", "max"),
        surf_totale=("SURF_TOTALE_ESTIMEE", "sum")
    ).reset_index()

    fam_colors = [PALETTE.get(f, "#7f7f7f") for f in acteurs_agg["FAMILLE_ACTEUR"]]
    sizes = np.clip(acteurs_agg["surf_totale"] / 100, 20, 400)

    scatter = ax2.scatter(
        acteurs_agg["nb_permis"],
        acteurs_agg["score_max"],
        c=fam_colors,
        s=sizes,
        alpha=0.65,
        edgecolors="none"
    )

    ax2.set_xlabel("Nombre de permis déposés par l'acteur dans le 78 (Récurrence)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Score de Pertinence Buddimm (0 à 100)", fontsize=11, fontweight="bold")
    ax2.set_title("Matrice Décisionnelle Buddimm : Récurrence vs Pertinence Métier\n(Taille des bulles = volume de m² développés)",
                  fontsize=12, fontweight="bold", pad=12)
    ax2.grid(True)

    # Annoter les acteurs majeurs dans le quadrant supérieur droit
    top_to_annotate = acteurs_agg[
        (acteurs_agg["score_max"] >= 70) & (acteurs_agg["nb_permis"] >= 10)
    ]
    for _, row in top_to_annotate.head(6).iterrows():
        ax2.annotate(
            row["DENOM_CLEAN"][:25],
            (row["nb_permis"], row["score_max"]),
            xytext=(row["nb_permis"] + 1, row["score_max"] - 2),
            fontsize=8,
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#333333", lw=0.7)
        )

    plt.tight_layout()
    out_path = os.path.join(OUTPUTS_DIR, "06_scoring_buddimm_matrice.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Figure 6 sauvegardée : {out_path}")


def export_crm_prospects(df):
    """Exporte la liste consolidée des organisations qualifiées pour le CRM Buddimm."""
    logger.info("Génération de l'export CRM pour la prospection...")

    # Agréger par organisation unique (SIREN + Dénomination)
    agg_dict = {
        "DENOM_CLEAN": "first",
        "NOM_OFFICIEL_SIRENE": "first",
        "FAMILLE_ACTEUR": "first",
        "SCORE_BUDDIMM": "max",
        "SEGMENT_BUDDIMM": "first",
        "NUM_DAU": "count",
        "SURF_TOTALE_ESTIMEE": "sum",
        "NB_LGT_TOT_CREES": "sum",
        "NB_LGT_PRET_LOC_SOCIAL": "sum",
        "PERMIS_FANTOME": "sum",
        "PROJET_MEDICO_SOCIAL": "sum",
        "EST_FINESS": "max",
        "EST_ESS": "max",
        "TYPE_SIAE": "first",
        "SIEGE_COMMUNE": "first",
        "SIEGE_CP": "first",
        "CATEGORIE_ENTREPRISE": "first",
        "TRANCHE_EFFECTIF": "first",
        "ANNEE_AUTORISATION": ["min", "max"]
    }

    crm = df.groupby("SIREN_CLEAN").agg(agg_dict)
    crm.columns = [
        "denomination_sitadel", "nom_officiel_sirene", "famille_acteur",
        "score_pertinence_buddimm", "segment_commercial", "nombre_permis_78",
        "surface_totale_m2", "logements_crees_totaux", "logements_sociaux_crees",
        "permis_fantomes_non_demarres", "projets_medico_sociaux",
        "statut_finess", "statut_ess", "statut_siae",
        "commune_siege", "cp_siege", "categorie_entreprise",
        "tranche_effectif", "premier_permis_annee", "dernier_permis_annee"
    ]

    crm = crm.reset_index().rename(columns={"SIREN_CLEAN": "siren"})

    # Nom d'affichage prioritaire
    crm["nom_prospect"] = crm["nom_officiel_sirene"].fillna(crm["denomination_sitadel"])

    # Statut récurrence
    def eval_recurrence(nb):
        if nb >= 5:
            return "GRAND_RECURRENT"
        elif nb >= 2:
            return "REGULIER"
        else:
            return "PONCTUEL"

    crm["profil_recurrence"] = crm["nombre_permis_78"].apply(eval_recurrence)

    # Type d'approche commerciale recommandée
    def recommend_approach(row):
        if row["segment_commercial"] == "TIER_1_HAUTE_PRIORITE":
            if row["permis_fantomes_non_demarres"] > 0:
                return "APPROCHE_AMO_RELANCE_CHANTIER"
            return "APPROCHE_DIRECTION_IMMOBILIERE_DELEGUEE"
        elif row["segment_commercial"] == "TIER_2_PRIORITAIRE":
            return "APPROCHE_DIAGNOSTIC_PATRIMOINE"
        elif row["segment_commercial"] == "TIER_3_VEILLE":
            return "VEILLE_APPELS_OFFRES"
        else:
            return "HORS_CIBLE"

    crm["action_commerciale_recommandee"] = crm.apply(recommend_approach, axis=1)

    # Tri par score de pertinence décroissant
    crm = crm.sort_values(
        by=["score_pertinence_buddimm", "nombre_permis_78", "surface_totale_m2"],
        ascending=[False, False, False]
    )

    crm.to_csv(CRM_EXPORT_PATH, index=False, sep=";")
    logger.info(f"Export CRM sauvegardé dans : {CRM_EXPORT_PATH} ({len(crm)} organisations répertoriées)")

    return crm


def generate_business_summary(df, crm):
    """Génère un rapport JSON structuré contenant tous les chiffres clés pour la note de synthèse."""
    logger.info("Génération de la synthèse métier chiffrée...")

    medico_acteurs = crm[crm["famille_acteur"] == "MEDICO_SOCIAL_SANTE"]
    social_acteurs = crm[crm["famille_acteur"] == "BAILLEUR_SOCIAL"]
    tier1_acteurs = crm[crm["segment_commercial"] == "TIER_1_HAUTE_PRIORITE"]
    tier2_acteurs = crm[crm["segment_commercial"] == "TIER_2_PRIORITAIRE"]

    top_medico_list = medico_acteurs.head(10)[[
        "nom_prospect", "siren", "nombre_permis_78", "surface_totale_m2",
        "permis_fantomes_non_demarres", "commune_siege", "statut_finess"
    ]].to_dict(orient="records")

    top_social_list = social_acteurs.head(10)[[
        "nom_prospect", "siren", "nombre_permis_78", "surface_totale_m2",
        "logements_sociaux_crees", "permis_fantomes_non_demarres", "commune_siege"
    ]].to_dict(orient="records")

    summary = {
        "departement": "Yvelines (78)",
        "periode": "2013-2026",
        "chiffres_globaux": {
            "total_permis_personnes_morales": len(df),
            "total_organisations_uniques": len(crm),
            "permis_volet_logement": int((df["VOLET_SITADEL"] == "LOGEMENT").sum()),
            "permis_volet_locaux": int((df["VOLET_SITADEL"] == "LOCAL").sum()),
            "surfaces_totales_creees_m2": int(df["SURF_TOTALE_ESTIMEE"].sum()),
            "total_permis_fantomes_bloques": int(df["PERMIS_FANTOME"].sum()),
            "taux_permis_fantomes": round(df["PERMIS_FANTOME"].mean(), 4)
        },
        "secteur_medico_social": {
            "nombre_permis": int((df["FAMILLE_ACTEUR"] == "MEDICO_SOCIAL_SANTE").sum()),
            "part_des_permis_pct": round((df["FAMILLE_ACTEUR"] == "MEDICO_SOCIAL_SANTE").mean() * 100, 2),
            "nombre_organisations_uniques": len(medico_acteurs),
            "organisations_recurrentes_gte_2": int((medico_acteurs["nombre_permis_78"] >= 2).sum()),
            "permis_fantomes_medico": int(medico_acteurs["permis_fantomes_non_demarres"].sum()),
            "surfaces_creees_m2": int(medico_acteurs["surface_totale_m2"].sum()),
            "top_10_organisations": top_medico_list
        },
        "secteur_logement_social": {
            "nombre_permis": int((df["FAMILLE_ACTEUR"] == "BAILLEUR_SOCIAL").sum()),
            "part_des_permis_pct": round((df["FAMILLE_ACTEUR"] == "BAILLEUR_SOCIAL").mean() * 100, 2),
            "nombre_organisations_uniques": len(social_acteurs),
            "organisations_recurrentes_gte_2": int((social_acteurs["nombre_permis_78"] >= 2).sum()),
            "permis_fantomes_social": int(social_acteurs["permis_fantomes_non_demarres"].sum()),
            "logements_sociaux_crees": int(social_acteurs["logements_sociaux_crees"].sum()),
            "top_10_organisations": top_social_list
        },
        "prospection_commerciale_buddimm": {
            "prospects_tier_1_haute_priorite": len(tier1_acteurs),
            "permis_couverts_tier_1": int(tier1_acteurs["nombre_permis_78"].sum()),
            "prospects_tier_2_prioritaire": len(tier2_acteurs),
            "permis_couverts_tier_2": int(tier2_acteurs["nombre_permis_78"].sum()),
            "chantiers_en_souffrance_cibles_amo": int(
                tier1_acteurs["permis_fantomes_non_demarres"].sum() +
                tier2_acteurs["permis_fantomes_non_demarres"].sum()
            )
        }
    }

    with open(SYNTHESE_METIER_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"Synthèse métier exportée dans : {SYNTHESE_METIER_PATH}")

    return summary


def run_analysis_pipeline():
    """Point d'entrée principal pour les analyses et visualisations."""
    setup_matplotlib()

    logger.info("Chargement des données classifiées...")
    df = pd.read_csv(INPUT_CLASSIFIED_PATH, sep=";", low_memory=False, dtype={"SIREN_CLEAN": str})
    df["SIREN_CLEAN"] = df["SIREN_CLEAN"].astype(str).str.replace(".0", "", regex=False).str.zfill(9)

    # Surfaces estimées
    df["SURF_TOTALE_ESTIMEE"] = df["SURF_HAB_CREEE"].fillna(0) + df["SURF_LOC_CREEE"].fillna(0)

    # Production des graphiques
    plot_01_distribution_familles(df)
    plot_02_top_acteurs_medicosocial_social(df)
    plot_03_dynamique_temporelle(df)
    plot_04_top_communes_78(df)
    plot_05_permis_fantomes_analyse(df)
    plot_06_scoring_buddimm_matrice(df)

    # Export CRM
    crm = export_crm_prospects(df)

    # Synthèse métier
    summary = generate_business_summary(df, crm)

    logger.info("=== ANALYSE TERMINÉE AVEC SUCCÈS ===")


if __name__ == "__main__":
    run_analysis_pipeline()
