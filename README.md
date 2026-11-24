# BUDDIMM — Cas d'Étude Sitadel Yvelines (78)
**Cartographie et qualification des demandeurs d'autorisations d'urbanisme pour le secteur médico-social et du logement social**

> **Candidat :** Marwane Hajjy  
> **Formation :** ENSIMAG / Master 2 MASH AI (Université Grenoble Alpes)  
> **Poste visé :** Stage de fin d'études / Ingénieur Data & IA — Buddimm  
> **Date de rendu :** Novembre 2026  
> **Note de synthèse (2 pages) :** [`docs/NOTE.md`](docs/NOTE.md) | Version PDF : [`docs/NOTE_SYNTHESE_BUDDIMM_78.pdf`](docs/NOTE_SYNTHESE_BUDDIMM_78.pdf)  
> **Journal de bord horodaté :** [`JOURNAL.md`](JOURNAL.md)

---

## 1. Contexte & Thèse Métier

Buddimm assure la direction immobilière externalisée et l'assistance à maîtrise d'ouvrage (AMO) pour les acteurs de l'Économie Sociale et Solidaire (ESS), en particulier le secteur médico-social et le logement social.

**Le constat :** La base ouverte Sitadel (Ministère de la Transition Écologique) recense l'ensemble des permis de construire délivrés en France, mais ne qualifie pas *la nature métier* du demandeur.
**La thèse :** En croisant les autorisations d'urbanisme des Yvelines (78) avec les registres d'entreprises (SIRENE, FINESS, ESS, SIAE), ce projet transforme une base administrative brute en un **moteur de veille et de prospection commerciale proactive** pour Buddimm :
1. **Cartographier l'écosystème** : identifier précisément les acteurs médico-sociaux et bailleurs sociaux du 78.
2. **Mesurer la récurrence** : distinguer les constructeurs réguliers des demandeurs occasionnels.
3. **Détecter les chantiers en souffrance (« permis fantômes »)** : repérer les projets autorisés depuis > 2 ans sans ouverture de chantier déclarée, cibles d'acquisition idéales pour une offre d'AMO et de relance.
4. **Calculer un Score de Pertinence Buddimm (0 à 100)** pour prioriser l'effort commercial.

---

## 2. Structure du Dépôt

```
buddimm-sitadel-78/
├── data/                                 # Données sources et enrichies
│   ├── sitadel_logements_78.csv          # Données brutes Sitadel Logements (20 205 lignes)
│   ├── sitadel_locaux_78.csv             # Données brutes Sitadel Locaux (7 887 lignes)
│   ├── sitadel_78_personnes_morales.csv  # Données filtrées Personnes Morales (9 572 lignes)
│   ├── cache_sirene.json                 # Cache local persistant des requêtes API
│   ├── sitadel_78_enriched.csv           # Données enrichies SIRENE/FINESS/ESS
│   └── sitadel_78_classified.csv         # Données classifiées avec Score Buddimm
│
├── scripts/                              # Pipeline data modulaire et reproductible
│   ├── 01_download_filter_sitadel.py     # Ingestion, filtrage 78 et normalisation SIREN
│   ├── 02_enrich_sirene.py               # Enrichissement SIRENE / Annuaire Entreprises
│   ├── 03_classify_families.py           # Classification 9 familles et scoring Buddimm (regex boundaries)
│   ├── 04_analyze_patterns.py            # Analyses quantitatives, 6 figures et export CRM
│   ├── 05_audit_classification.py        # Audit qualité et validation croisée sur 20 cas (100% conformes)
│   └── run_pipeline.py                   # Orchestrateur global (exécute les 5 étapes en ~5.8s)
│
├── outputs/                              # Livrables graphiques, statistiques et exports
│   ├── 01_distribution_familles.png      # Fig 1 : Distribution des permis et surfaces par famille
│   ├── 02_top_acteurs_medicosocial_social.png # Fig 2 : Top 20 acteurs médico-sociaux et bailleurs
│   ├── 03_dynamique_temporelle.png       # Fig 3 : Évolution annuelle 2013-2025 par famille
│   ├── 04_top_communes_78.png            # Fig 4 : Concentration géographique communale
│   ├── 05_permis_fantomes_analyse.png    # Fig 5 : Analyse des permis non démarrés (chantiers bloqués)
│   ├── 06_scoring_buddimm_matrice.png    # Fig 6 : Matrice Récurrence vs Score Buddimm
│   ├── crm_export_prospects_buddimm.csv  # Export CRM qualifié (4 780 organisations répertoriées)
│   ├── audit_classification_20_permis.json # Rapport d'audit qualité (20 cas contrôlés manuellement)
│   ├── stats_ingestion_78.json           # Métriques d'ingestion et complétude
│   ├── stats_enrichment_sirene.json      # Métriques d'enrichissement API
│   ├── stats_classification_78.json      # Métriques de classification
│   └── synthese_metier_buddimm.json      # KPIs consolidés pour le comité de direction
│
├── docs/                                 # Documents de synthèse
│   ├── NOTE.md                           # Note de synthèse de 2 pages (format Markdown sourcé)
│   ├── NOTE_SYNTHESE_BUDDIMM_78.pdf      # Note de synthèse au format PDF (strictement 2 pages)
│   └── compact_header.tex                # Configuration de mise en page LaTeX
│
├── RAPPORT_AUTOEVALUATION.md             # Grille d'auto-évaluation et plan d'action exécuté
├── JOURNAL.md                            # Journal de bord horodaté retraçant la démarche
└── README.md                             # Documentation principale du projet
```

---

## 3. Reproduction Rapide en 1 Commande

Le projet est conçu pour une exécution 100% autonome et déterministe.

### Prérequis
- Python 3.10+
- Dépendances Python : `pandas`, `numpy`, `requests`, `matplotlib`

```bash
# Cloner le dépôt
git clone https://github.com/MarOuan20004/buddimm-sitadel-78.git
cd buddimm-sitadel-78

# Lancer le pipeline complet de bout en bout (5 étapes)
python3 scripts/run_pipeline.py
```

*Temps d'exécution mesuré : **5.85 secondes** (incluant l'audit qualité).*

---

## 4. Chiffres Clés du Marché de la Construction dans le 78 (2013 — nov. 2026)

| Indicateur | Valeur chiffrée | Signification métier pour Buddimm | Source |
|:---|:---:|:---|:---|
| **Total autorisations 78** | **28 092** | 20 205 logements et 7 887 locaux créés | API DiDo SDES (DEP_CODE=78) |
| **Permis Personnes Morales** | **9 572 (34.1%)** | Périmètre strict B2B / institutionnel (100% SIREN vérifiés) | `outputs/stats_ingestion_78.json` |
| **Organisations uniques** | **4 780** | Base totale d'acteurs de la construction dans le département | `outputs/stats_ingestion_78.json` |
| **Médico-Social & Santé** | **470 permis (4.9%)** | **358 942 m²** développés par 130 organisations sanitaires et sociales | `outputs/synthese_metier_buddimm.json` |
| **Bailleurs Sociaux** | **735 permis (7.7%)** | **9 988 logements sociaux créés** par 174 organismes HLM/OPH/ESH | `outputs/synthese_metier_buddimm.json` |
| **Permis « fantômes » (bloqués > 2 ans)** | **3 490 (36.5%)** | Dont **170 en médico-social** et **202 en HLM** $\rightarrow$ **Cibles prioritaires AMO** | `outputs/synthese_metier_buddimm.json` |
| **Prospects TIER 1 (Score ≥ 70)** | **44 organisations** | **441 permis couverts** (Fondation Mallet, Bellan, Immobilière 3F, Seqens...) | `outputs/crm_export_prospects_buddimm.csv` |
| **Prospects TIER 2 (Score 45-69)** | **270 organisations** | **1 063 permis couverts** (Associations locales, bailleurs régionaux) | `outputs/crm_export_prospects_buddimm.csv` |

---

## 5. Visualisations Décisionnelles Produites

Les 6 visualisations haute résolution (300 DPI) générées dans le dossier `outputs/` illustrent les dynamiques du département :

1. **`outputs/01_distribution_familles.png`** : Répartition des 9 572 permis et des m² de plancher entre les 9 familles d'acteurs.
2. **`outputs/02_top_acteurs_medicosocial_social.png`** : Palmarès des 20 acteurs médico-sociaux, fondations et bailleurs sociaux les plus actifs dans le 78.
3. **`outputs/03_dynamique_temporelle.png`** : Courbes annuelles 2013-2025 mettant en lumière la résilience du secteur médico-social face aux crises (COVID 2020 et choc des taux 2023-2024).
4. **`outputs/04_top_communes_78.png`** : Cartographie des communes phares (Versailles, Saint-Germain-en-Laye, Mantes-la-Jolie, Poissy, Trappes, Richebourg).
5. **`outputs/05_permis_fantomes_analyse.png`** : Taux de chantiers non démarrés par famille et identification des porteurs de projets en souffrance.
6. **`outputs/06_scoring_buddimm_matrice.png`** : Matrice décisionnelle croisant la récurrence de l'acteur et son Score de Pertinence Buddimm.

---

## 6. Audit Qualité & Conformité de la Taxonomie (Validation sur 20 cas)

Afin d'éprouver la rigueur de l'arbre de décision et d'éliminer tout soupçon de « boîte noire », un audit délibéré sur **20 permis représentatifs des 9 familles** est intégré nativement dans le pipeline via `scripts/05_audit_classification.py` :

- **Échantillon :** 4 médico-social (Fondation Mallet, Fondation Bellan, Avenir APEI, L'Arche d'Aigrefoin), 3 bailleurs sociaux (Immobilière 3F, Domnis, Les Résidences), 2 associations ESS, 2 collectivités (Conseil Départemental 78, Commune de Versailles), 3 promoteurs (Bouygues, Kaufman, SCCV projet), 2 SCI patrimoniales, 2 réseaux (Enedis, SNCF), 1 entreprise privée, 1 non déterminé.
- **Résultat :** **20/20 cas conformes (100.0% de précision)** vérifiés sur la base des dénominations, codes APE, codes Catégories Juridiques et statuts FINESS/SIRENE officiels.
- **Rapport exporté :** [`outputs/audit_classification_20_permis.json`](outputs/audit_classification_20_permis.json).

---

## 7. Méthodologie de Scoring Buddimm

Chaque autorisation et organisation reçoit un **Score de Pertinence Buddimm (0 à 100)** calculé par cumul pondéré :

$$\text{Score} = \text{Base Famille} (0\text{ à }45) + \text{Accréditation ESS/FINESS} (0\text{ à }25) + \text{Typologie Bâti} (0\text{ à }20) + \text{Permis Bloqué} (10) + \text{Récurrence} (0\text{ à }10)$$

- **Tier 1 — Haute Priorité ($\ge 70$) :** Grands acteurs médico-sociaux et bailleurs sociaux récurrents avec chantiers actifs ou bloqués $\rightarrow$ *Offre de direction immobilière déléguée et AMO.*
- **Tier 2 — Prioritaire ($45-69$) :** Associations gestionnaires, fondations et bailleurs régionaux $\rightarrow$ *Offre de diagnostic immobilier et audit énergétique.*
- **Tier 3 — Veille ($25-44$) :** Collectivités territoriales et promoteurs privés avec mixité sociale $\rightarrow$ *Veille sur les avis d'appels d'offres.*
- **Hors Cible ($< 25$) :** Opérateurs réseaux (Enedis, SNCF), entreprises commerciales et SCI privées $\rightarrow$ *Non prospectés.*

---

## 8. Sources Publiques Utilisées

| Source | Fournisseur | Licence | Usage dans le projet |
|:---|:---|:---:|:---|
| **Base Sitadel (Logements & Locaux)** | SDES / Ministère de la Transition Écologique via API DiDo | Licence Ouverte 2.0 (Etalab) | Données maîtresses des permis de construire 2013-2026 |
| **API Recherche d'Entreprises** | DINUM / Insee (`recherche-entreprises.api.gouv.fr`) | Licence Ouverte 2.0 (Etalab) | Statuts officiels FINESS, ESS, SIAE, raison sociale, effectifs |
| **Nomenclature NAF Rév. 2 / APE** | Insee | Libre | Détection des activités de santé (86.*), médico-social (87.*, 88.*), HLM (68.20A) |
| **Nomenclature des Catégories Juridiques** | Insee | Libre | Détection OPH (5546), SA d'HLM (5202), Associations (9220), Fondations (9300) |
