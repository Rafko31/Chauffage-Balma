# Pulse IA - Module Adoption IA (MVP)

Ce projet est le MVP du produit SaaS Pulse IA, conçu pour les chambres de commerce et organisations similaires au Québec pour piloter l'adoption de l'IA au sein de leurs organisations ou membres.

## Fonctionnalités Clés

- **Architecture Multi-tenant** : Isolation complète des données par organisation.
- **Anonymat Strict** : Séparation logique entre l'identité des participants et leurs réponses. Pas de lien technique pour les réponses anonymes.
- **Courbe d'Adoption** : Suivi via 6 états (Exposition, Exploration, Expérimentation, Usage utile, Intégration, Diffusion).
- **Import CSV Idempotent** : Chargement de populations avec mapping de colonnes flexible.
- **Registre des Cas d'Usage** : Suivi léger de l'Idée à la Diffusion.
- **Génération de Rapports (Report-First)** : Workflow de validation (Brouillon -> Publié) et génération de rapports de gouvernance PDF.
- **Seuils de Confidentialité** : Masquage automatique des résultats agrégés si le nombre de répondants est inférieur au seuil configuré.

## Structure du Projet

- `src/pulse_ia/models/` : Schémas de base de données (SQLAlchemy).
- `src/pulse_ia/services/` : Logique métier (Survey, Analytics, Report, Import, UseCase).
- `src/pulse_ia/schemas/` : Schémas de validation Pydantic.
- `src/pulse_ia/scripts/` : Scripts utilitaires (ex: seed demo data).
- `src/pulse_ia/tests/` : Suite complète de tests d'acceptation.

## Installation et Test Rapide

1. Installer les dépendances : `pip install -r requirements.txt`
2. Lancer la démo avec données fictives (SQLite) :
   `DATABASE_URL=sqlite:///./pulse_ia.db python -m src.pulse_ia.scripts.seed_demo`
3. Exécuter les tests :
   `DATABASE_URL=sqlite:///./test.db python -m pytest src/pulse_ia/tests/`

## Organisation Fictive de Démo
Le script de seed utilise **Manufacture Innovante Inc.** comme organisation fictive pour démontrer la chaîne complète : import -> collecte -> analyse -> recommandations.
