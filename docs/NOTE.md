# NOTE DE SYNTHÈSE BUDDIMM — CAS SITADEL 78
**Cartographie et qualification des demandeurs d'autorisations d'urbanisme dans les Yvelines**  
*Auteur : Marwane Hajjy (ENSIMAG / Master 2 MASH AI Univ. Grenoble Alpes) — Novembre 2026*  
*Dépôt Git : [github.com/MarOuan20004/buddimm-sitadel-78](https://github.com/MarOuan20004/buddimm-sitadel-78)*

---

### 1. Mon angle d'attaque et ma thèse métier

> **Ma thèse :** La base Sitadel recense qui construit, mais ignore la nature exacte du demandeur et ses besoins d'accompagnement. En croisant les autorisations d'urbanisme des Yvelines avec les registres officiels SIRENE et FINESS, j'ai cartographié l'écosystème médico-social et du logement social du 78 : j'isole les acteurs réguliers, quantifie leur effort de construction et détecte les chantiers bloqués (« permis fantômes ») pour transformer une base administrative passive en un moteur de prospection commerciale directement actionnable pour Buddimm.

Mon angle répond aux enjeux d'un gestionnaire immobilier externalisé et AMO dédié à l'ESS : repérer les associations médico-sociales et les bailleurs sociaux en amont de leurs projets, et approcher les porteurs de permis en souffrance avec une offre ciblée de déblocage opérationnel.

---

### 2. Résultats principaux et enseignements chiffrés (2013 — novembre 2026)

Sur **28 092 autorisations d'urbanisme** délivrées dans les Yvelines (20 205 logements, 7 887 locaux) *[Source : API DiDo SDES]* , j'ai isolé **9 572 permis de Personnes Morales** (3 696 en logements, 5 876 en locaux) représentant **4 780 organisations distinctes** (100% SIREN normalisés) *[Source : outputs/stats_ingestion_78.json]*.

| Famille d'acteurs | Permis PM | Part (%) | Rôle clé et volumes structurants |
|:---|:---:|:---:|:---|
| **Entreprises privées tertiaires & indus.** | 2 423 | 25.3% | 4 480 500 m² de locaux d'activité et sièges pour compte propre |
| **SCI & Foncières privées (patrimoniales)** | 2 269 | 23.7% | 2 411 120 m² de gestion locative et patrimoniale privée |
| **Promoteurs immobiliers privés (dont SCCV)** | 1 583 | 16.5% | 2 890 400 m² en résidentiel collectif (Bouygues, Kaufman, Nexity) |
| **Collectivités & Établissements publics** | 1 360 | 14.2% | 1 685 300 m² d'équipements publics (Communes, Conseil Départemental 78) |
| **Bailleurs sociaux (SA HLM, OPH, ESH)** | 735 | 7.7% | **9 988 lgts sociaux créés** (519 280 m² : 3F, Les Résidences, Seqens, Domnis) |
| **Opérateurs Réseaux & Transports** | 499 | 5.2% | 198 450 m² d'infrastructures (Enedis, SNCF, RTE, RATP, télécoms) |
| **Médico-Social & Santé (ESMS, FINESS)** | 470 | 4.9% | **358 942 m²** portés par **130 organisations** (EHPAD, cliniques, foyers) |
| **Associations & Fondations ESS** | 231 | 2.4% | 51 820 m² d'équipements associatifs, cultuels et caritatifs |
| **Non déterminé / Données incomplètes** | 2 | 0.02% | 99 m² (cas résiduels radiés) *[outputs/stats_classification_78.json]* |

#### A. Le gisement médico-social et solidaire dans le 78
- J'ai répertorié **470 autorisations d'urbanisme** portées par **130 organisations sanitaires et sociales** (358 942 m² de plancher) *[Source : outputs/synthese_metier_buddimm.json]*.
- **57 organisations sont récurrentes** (au moins 2 permis dans le 78), constituant le cœur de prospection Buddimm.
- **Top acteurs prioritaires identifiés :**
  - **Fondation Mallet** : 40 permis (14 095 m²), Richebourg (soins, rééducation, polyhandicap). Fait marquant : 29 permis n'ont pas de Déclaration d'Ouverture de Chantier (DOC) *[SIREN 775667181, FINESS]* .
  - **Fondation Léopold Bellan** : 13 permis (14 708 m²), EHPAD et résidences polyhandicap *[SIREN 775672165]* .
  - **Avenir APEI** : 12 permis (3 707 m²), Carrières-sur-Seine (ESAT, foyers d'accueil médicalisés) *[SIREN 785039058]* .
  - **Association L'Arche d'Aigrefoin** : 11 permis (2 838 m²), Saint-Rémy-lès-Chevreuse (habitat inclusif handicap) *[SIREN 340800754]* .
  - **APAJH Yvelines** (8 permis), **SEAY** (8 permis à Versailles), **A.R.I.S.S.E** (7 permis), **Delos APEI 78** (6 permis), **Croix-Rouge** (5 permis).

#### B. Les bailleurs sociaux (HLM / ESH / OPH)
- J'ai identifié **735 permis** portés par **174 organismes**, totalisant **9 988 logements sociaux créés** *[outputs/synthese_metier_buddimm.json]*.
- Concentration autour de leaders régionaux : **Immobilière 3F** (54 permis, 105 631 m², 1 358 lgts), **Les Résidences Yvelines / Essonne** (47 permis, 53 654 m²), **Seqens** (38 permis, 75 191 m²), **Domnis** (36 permis, 51 525 m²), **Antin Résidences** (32 permis, 99 443 m²), **OPIEVOY** (18 permis).

#### C. L'opportunité des « permis fantômes » (Chantiers bloqués > 2 ans)
- J'ai détecté **3 490 permis** autorisés depuis plus de 2 ans sans aucune DOC dans Sitadel (36.5% des permis PM).
- Parmi eux, **170 permis médico-sociaux** et **202 permis de bailleurs sociaux** sont en souffrance *[outputs/synthese_metier_buddimm.json]*. Ces retards traduisent des impasses financières ou techniques : c'est un levier d'acquisition prioritaire pour une offre AMO de relance.

---

### 3. Logique de classification et arbre de décision hiérarchique

Pour qualifier les demandeurs sans opacité, j'ai implémenté un arbre déterministe hiérarchique à 4 niveaux :
- **Niveau 1 — Réseaux :** Enedis, SNCF, RTE, RATP via expressions régulières à frontières de mots (`\bRTE\b`, `\bSNCF\b`).
- **Niveau 2 — Médico-Social & Santé :** Drapeaux officiels API FINESS, type SIAE (ESAT/EA), codes APE santé (`86.*`, `87.*`, `88.*`) ou mots-clés sanitaires.
- **Niveau 3 — Bailleurs Sociaux :** Catégories juridiques HLM (`5202`, `5546`, `5550`), dénominations connues et APE `68.20A` avec logements sociaux.
- **Niveau 4 — Collectivités & Autres :** CJ `71-74` (Communes, CD78) $\rightarrow$ Promoteurs (`41.10`) $\rightarrow$ ESS (`9220`) $\rightarrow$ SCI (`6540/6541`) $\rightarrow$ Tertiaire.
- *Validation empirique :* J'ai audité manuellement un échantillon de 20 permis : **100.0% de conformité** vérifiée *[Source : outputs/audit_classification_20_permis.json]*.

---

### 4. Ce que je n'ai pas réussi à faire, pièges résolus et fragilités assumées

En toute transparence vis-à-vis des critères d'évaluation du brief, voici les 4 difficultés et arbitrages de mon travail :
1. **Rate-limiting API Recherche d'Entreprises :** Lors des requêtes concurrentes sur 4 780 SIRENs, l'API DINUM a renvoyé des erreurs `429` et `ConnectTimeout`. **Mon arbitrage :** J'ai conçu un cache JSON local (`data/cache_sirene.json`) enrichissant 300 SIRENs prioritaires (couvrant 36.6% des permis et 100% des têtes de réseau médico-sociales et HLM). Pour les autres, j'ai bâti un fallback déterministe sur les colonnes Sitadel (`CJ_DEM`, `APE_DEM` complétées à 99.95%), garantissant un pipeline résilient et autonome.
2. **Gotcha booléen `np.nan` dans Pandas :** En Python, `bool(np.nan) == True` et `str(np.nan) == 'nan'`. Ma première passe évaluait la condition SIAE à `True` sur les valeurs manquantes. Détecté lors de l'audit de distribution, j'ai corrigé ce biais via des helpers défensifs `safe_get_*`.
3. **Piège du substring matching débusqué par mon audit manuel :** Lors de mon premier audit, 131 permis du Département 78 étaient versés à tort dans les Réseaux : l'acronyme `RTE` matchait dans « depa**rte**ment » et `IME` dans « bât**ime**nt ». J'ai résolu ce bug en imposant des frontières de mots (`\bRTE\b`, `\bIME\b`), rétablissant l'exactitude des collectivités (1 360 permis) et du médico-social (470 permis).
4. **Opacité des SCCV de promoteurs :** Les promoteurs créent une SCCV par opération. Sans accès au Registre des Bénéficiaires Effectifs (RBE/INPI), je n'ai pu rattacher automatiquement 100% des filiales à leur société-mère (ex. Bouygues, Kaufman).

---

### 5. Extension : Workflow de prospection commerciale CRM Buddimm

J'ai modélisé un workflow opérationnel en 4 phases pour alimenter le CRM Buddimm :
- **Phase 1 — Ingestion :** Flux mensuel DiDo Sitadel 78 $\rightarrow$ Filtrage Personnes Morales (100% SIREN normalisés).
- **Phase 2 — Qualification & Scoring :** Réconciliation FINESS / SIRENE $\rightarrow$ Calcul du **Score de Pertinence Buddimm (0 à 100)**.
- **Phase 3 — Triangulation commerciale :**
  - *Tier 1 (Haute Priorité — Score $\ge 70$, 44 acteurs / 441 permis)* : Fondations (Mallet, Bellan), Bailleurs récurrents (3F, Seqens) $\rightarrow$ *Offre de direction immobilière externalisée.*
  - *Tier 2 (Prioritaire — Score 45-69, 270 acteurs / 1 063 permis)* : Associations gestionnaires, bailleurs régionaux $\rightarrow$ *Offre de diagnostic et audit de parc.*
  - *Signal d'opportunité « Chantiers bloqués » (528 projets cibles AMO)* : Permis autorisés > 2 ans sans DOC $\rightarrow$ *Offre d'assistance au déblocage de chantier.*
- **Phase 4 — Activation CRM :** Injection de `outputs/crm_export_prospects_buddimm.csv` (4 780 comptes) dans HubSpot/Salesforce.

---

### 6. Méthodologie, temps passé et outils mobilisés

- **Temps total :** ~3h20 (1h cadrage/exploration DiDo, 1h15 pipeline et enrichissement API, 1h05 analyses, audit 20 cas, graphiques 300 DPI et rédaction).
- **Outils :** Python 3.12 (Pandas, NumPy, Requests, Matplotlib), API DiDo (Ministère Écologie), API Recherche d'Entreprises (DINUM / Insee), Pandoc, LaTeX, Git.
- **Transparence IA :** Utilisation de l'environnement Antigravity pour accélérer le prototypage des expressions régulières et l'orchestration du pipeline.
