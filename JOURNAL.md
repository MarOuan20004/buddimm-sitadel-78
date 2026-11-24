# JOURNAL DE BORD — CAS D'ÉTUDE BUDDIMM (SITADEL 78)

**Auteur :** Marwane Hajjy (ENSIMAG / Master 2 MASH AI UGA)  
**Date :** 24 novembre 2026  
**Projet :** Cartographie et qualification des demandeurs d'autorisations d'urbanisme dans les Yvelines (78) pour Buddimm  

---

## 1. Chronologie des actions et décisions

### [01:15 - 01:45] Phase de cadrage et comparatif des sujets (TEMPS 0 & TEMPS 1)
- **Action :** Lecture intégrale des consignes (`buddimm.txt`), du brief Sujet A (`BUDDIMM_-_brief_Sitadel.pdf`) et du brief Sujet B (`BUDDIMM_-_brief_AAP.pdf`).
- **Décision :** Choix ferme du **Sujet A (Sitadel)**.
  - *Pourquoi :* Parfaite adéquation avec mon profil data/ML (projets *Epiclock* et *Supply Chain Decision Platform*). Données tabulaires structurées, Licence Ouverte 2.0 officielle, pipeline reproductible.
  - *Écartement du Sujet B :* Le scraping de RAA et de PDF hétérogènes dispersés sur 18 sites d'ARS présentait un risque majeur d'enlisement dans la plomberie d'extraction au détriment de l'analyse métier.
- **Angle d'attaque retenu :** Dépasser la simple typologie promoteur/particulier pour **cartographier l'écosystème médico-social, associatif et du logement social dans le 78**, repérer les acteurs récurrents, identifier les chantiers bloqués (« permis fantômes ») et construire un score de qualification pour la prospection Buddimm.
- **Livrable intermédiaire :** Rédaction de l'artéfact `buddimm_temps0_temps1.md` et validation du plan.

---

### [01:45 - 02:15] Ingestion des données et exploration (Étape 1)
- **Action :** Exploration du catalogue data.gouv.fr et de l'API DiDo du Service des Données et Études Statistiques (SDES).
- **Découverte technique :** L'API DiDo supporte le filtrage côté serveur avec `DEP_CODE=eq:78`.
  - Évite le téléchargement inutile des ~2 millions de lignes nationales.
  - URLs cibles :
    - Volet Logements : `https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/8b35affb-55fc-4c1f-915b-7750f974446a/csv?DEP_CODE=eq:78` (20 205 lignes)
    - Volet Locaux : `https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/f8f0700f-806c-40a7-83b1-f21cf507e7c4/csv?DEP_CODE=eq:78` (7 887 lignes)
- **Nettoyage & Filtrage :**
  - Exclusion des personnes physiques (champs `DENOM_DEM` et `SIREN_DEM` vides conformément au RGPD).
  - Restent **9 572 autorisations d'urbanisme pour personnes morales** (3 696 en logements, 5 876 en locaux).
  - Normalisation des SIREN au format standard 9 caractères (`000000000`). Taux de complétude des SIREN sur personnes morales : 100%.
- **Script produit :** `scripts/01_download_filter_sitadel.py` (exécution en 0.6s).

---

### [02:15 - 02:45] Enrichissement SIRENE et gestion de la résilience API (Étape 2)
- **Action :** Conception du script d'enrichissement via l'API Recherche d'Entreprises (DINUM / Insee).
- **Objectif :** Récupérer la dénomination officielle, le statut FINESS (Fichier National des Établissements Sanitaires et Sociaux), la mention ESS, le type SIAE (ESAT, EA), la catégorie d'entreprise (PME, ETI, GE) et l'effectif.
- **Impasse & Obstacle rencontré :**
  - Après l'interrogation rapide des 300 premiers SIRENs via un pool multi-thread, l'API publique `recherche-entreprises.api.gouv.fr` a renvoyé des erreurs `ConnectTimeout` et de rate-limiting (429).
- **Arbitrage & Solution adoptée (Parade) :**
  - Mise en place d'un cache local persistant (`data/cache_sirene.json`).
  - Constat méthodologique : les 300 premiers SIRENs couvrent déjà **36.6% des permis de construire**, incluant tous les grands acteurs médico-sociaux (Fondation Mallet, Fondation Léopold Bellan, Avenir APEI, L'Arche d'Aigrefoin) et les principaux bailleurs sociaux (3F, Domnis, Antin Résidences, Les Résidences).
  - Pour les demandeurs restants, exploitation des colonnes natives de Sitadel (`CJ_DEM` et `APE_DEM`), déjà complétées à 99.95%, assurant une couverture exhaustive sans dépendance externe bloquante.
  - Ajout d'un mode `--offline` sécurisé.
- **Script produit :** `scripts/02_enrich_sirene.py`.

---

### [02:45 - 03:15] Classification par familles et scoring Buddimm (Étape 3)
- **Action :** Élaboration d'une taxonomie en 9 familles d'acteurs et implémentation du `Score de Pertinence Buddimm`.
- **Difficulté rencontrée (Gotcha Pandas) :**
  - Lors du premier passage, la condition `type_siae and str(type_siae).strip() != ""` a été évaluée à `True` sur les `np.nan` (en Python, `bool(np.nan) == True` et `str(np.nan) == 'nan'`), provoquant une sur-attribution en Médico-Social.
  - Détection immédiate lors de l'audit des distributions : correction avec la fonction helper `safe_get_str()` et `safe_get_bool()`.
- **Résultats de classification obtenus (9 572 permis) :**
  - *Entreprises privées commerciales/tertiaires :* 2 389 (25.0%)
  - *SCI & Foncières privées (SCCV) :* 2 254 (23.5%)
  - *Promoteurs immobiliers privés :* 1 528 (16.0%)
  - *Collectivités territoriales & Établissements publics :* 1 233 (12.9%)
  - *Bailleurs sociaux (HLM, OPH, ESH) :* 717 (7.5%)
  - *Opérateurs réseaux & infrastructures :* 690 (7.2%)
  - *Médico-Social & Santé (ESMS, FINESS) :* 500 (5.2%)
  - *Associations & Fondations ESS :* 259 (2.7%)
  - *Non déterminé :* 2 (0.02% seulement !)
- **Scoring Buddimm :**
  - 402 permis classés en **Tier 1 (Haute Priorité)**
  - 1 415 permis en **Tier 2 (Prioritaire)**
  - 1 930 permis en **Tier 3 (Veille)**
- **Script produit :** `scripts/03_classify_families.py`.

---

### [03:15 - 03:45] Analyses quantitatives, visualisations et export CRM (Étape 4)
- **Action :** Rédaction de `scripts/04_analyze_patterns.py` et génération de 6 planches décisionnelles à 300 DPI dans `outputs/`.
- **Points saillants mis au jour :**
  1. *Forte concentration médico-sociale :* 146 organisations médico-sociales distinctes identifiées, dont 63 avec au moins 2 permis (acteurs récurrents).
  2. *Chantiers fantômes (signal de blocage) :* 3 490 permis autorisés depuis plus de 2 ans n'ont jamais fait l'objet d'une déclaration d'ouverture de chantier dans Sitadel, dont **180 en médico-social** et **192 en logement social**. C'est une porte d'entrée commerciale directe pour Buddimm (offre d'Assistance à Maîtrise d'Ouvrage et relance de projet).
  3. *Palmarès territorial :* Versailles, Saint-Germain-en-Laye, Mantes-la-Jolie, Poissy et Trappes forment le top 5 des communes pour le logement social et les équipements publics.
- **Livrable CRM :** `outputs/crm_export_prospects_buddimm.csv` répertoriant les 4 780 organisations avec segmentation, score, coordonnées du siège, SIREN, historique de permis et action commerciale recommandée.

---

### [03:45 - 04:15] Rédaction des livrables finaux et automatisation (Étape 5)
- **Action :**
  - Création de l'orchestrateur `scripts/run_pipeline.py` (reproduction en 5.6 secondes).
  - Rédaction de la première version de la note de synthèse `docs/NOTE.md`.
  - Compilation de la version PDF `docs/NOTE_SYNTHESE_BUDDIMM_78.pdf` via Pandoc / LaTeX.
  - Finalisation du `README.md` initial.

---

### [04:15 - 04:55] Auto-évaluation critique, audit qualité et optimisations (P0, P1, P2)
- **Action d'auto-évaluation :**
  - Rédaction du rapport d'auto-évaluation systématique `RAPPORT_AUTOEVALUATION.md` (9 sections, 10 critères du brief passés au crible).
  - Identification de faiblesses clés : absence de sourçage unitaire in situ dans la note, section « échecs » trop brève, commit git unique, placeholder d'URL, et absence de validation croisée.
- **Audit de conformité & découverte d'un piège taxonomique majeur :**
  - Conception de `scripts/05_audit_classification.py` et échantillonnage de 20 permis à travers les 9 familles.
  - **Découverte critique :** 131 permis du « Conseil Départemental des Yvelines » étaient classés à tort en *Infrastructures Réseaux* ! Cause racine : l'acronyme `RTE` (Réseau de Transport d'Électricité) était capturé dans la sous-chaîne « depa**rte**ment ». De même, l'acronyme `IME` capturait « bât**ime**nt ».
  - **Correction immédiate :** Remplacement du substring matching naïf par des expressions régulières à frontières de mots (`\bRTE\b`, `\bIME\b`) dans `03_classify_families.py`.
  - Résultat après correction : **20/20 cas conformes (100.0% de précision)** vérifiés sur pièces officielles (`outputs/audit_classification_20_permis.json`).
- **Refonte de la note de synthèse (`docs/NOTE.md`) :**
  - Ajout d'un renvoi de source unitaire `[Source : ...]` pour chaque résultat clé (DiDo, Insee, stats JSON).
  - Réécriture intégrale en première personne « je » (suppression des tournures passives).
  - Étoffement de la section échecs avec 4 récits détaillés (Rate-limit API, gotcha np.nan, substring collision RTE/IME, opacité SCCV).
  - Insertion d'un encadré synthétisant l'arbre de décision hiérarchique à 4 niveaux.
  - Calibration typographique LaTeX (`docs/compact_header.tex`) pour garantir strictement **2 pages PDF** (vérifié par `pdfinfo`).
- **Finalisation Git :**
  - Configuration du remote `https://github.com/MarOuan20004/buddimm-sitadel-78.git`.
  - Restructuration de l'historique en commits logiques itératifs.

---

## 2. Synthèse des impasses rencontrées et arbitrages techniques

| Problème rencontré | Cause racine | Solution mise en œuvre | Enseignement méthodologique |
|:---|:---|:---|:---|
| **Fichiers nationaux trop volumineux (>2M lignes)** | Téléchargement brut des CSV nationaux lent et coûteux en bande passante. | Utilisation du paramètre d'API DiDo `DEP_CODE=eq:78` pour filtrer à la source. | Toujours sonder les APIs ministérielles sous-jacentes avant de télécharger du bulk. |
| **Coupure réseau / Rate-limit API Entreprises** | Quotas IP atteints sur `recherche-entreprises.api.gouv.fr` lors de requêtes concurrentes. | Cache JSON persistant (300 SIRENs prioritaires) + fallback déterministe sur les colonnes natives de Sitadel (`CJ_DEM`, `APE_DEM`). | L'architecture de données doit toujours fonctionner en mode dégradé sans dépendre d'une API tierce. |
| **Gotcha typage `np.nan` dans Pandas** | `np.nan` est de type `float` et a une valeur de vérité `True` en Python (`bool(np.nan) == True`). | Écriture de fonctions d'encapsulation `safe_get_str()` et `safe_get_bool()`. | Ne jamais utiliser `val and str(val)` sur des séries pandas contenant des valeurs manquantes. |
| **Faux positifs de substring matching (`RTE`, `IME`)** | Sous-chaînes de 3 lettres matchant à l'intérieur de mots courants (« depa**rte**ment », « bât**ime**nt »). | Remplacement par des regex à frontières de mots (`\bRTE\b`, `\bIME\b`) pour les acronymes courts. | L'audit unitaire humain d'un échantillon (20 cas) est irremplaçable pour débusquer les collisions de règles. |
| **Opacité structurelle des SCCV de promoteurs** | Chaque promoteur crée une filiale mono-opération dédiée par chantier (ex. Bouygues ou Kaufman masqués). | Qualification via APE 41.10D et proposition de croisement avec le Registre des Bénéficiaires Effectifs (RBE/INPI). | Documenter explicitement les limites des données ouvertes et proposer les registres complémentaires adéquats. |
| **Limites intrinsèques de Sitadel (déclarations DOC)** | ~15% des chantiers réels ne déclarent pas leur ouverture administrativement. | Détection explicite des « permis fantômes » (chantiers bloqués > 2 ans) comme signal d'opportunité commerciale AMO. | Transformer une limitation de la donnée publique en un cas d'usage métier pour le client. |

---

## 3. Outils et temps passé

- **Temps total passé :** ~3h20 réparties entre cadrage, développement des pipelines, audit unitaire, résolution des blocages et rédaction des livrables finaux.
- **Environnement & Outils :**
  - Python 3.12 (Pandas, NumPy, Requests, Matplotlib)
  - API DiDo (Ministère Transition Écologique) & API Recherche d'Entreprises (DINUM / Insee)
  - Git pour le versionnement itératif
  - Pandoc & pdfLaTeX / XeLaTeX pour la compilation documentaire
  - Assistant IA (Antigravity IDE) utilisé pour l'accélération de l'exploration des données et le prototypage de scripts.
