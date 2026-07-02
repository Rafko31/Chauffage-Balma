# Pulse IA - Backend de Pilotage de l'Adoption de l'IA

Pulse IA est une plateforme SaaS permettant de mesurer, analyser et piloter l'adoption de l'Intelligence Artificielle au sein des organisations.

## 🚀 Démarrage Rapide (Démonstration)

Le projet inclut une configuration Docker complète pour une reproductibilité immédiate.

```bash
# 1. Lancer l'infrastructure (DB + API + Seed de données fictives)
docker-compose up --build

# 2. Accéder à l'API
# L'API est disponible sur http://localhost:8000
# La documentation Swagger est sur http://localhost:8000/docs
```

La commande `docker-compose up` effectue automatiquement :
- La montée des migrations Alembic.
- Le seed des données pour l'organisation fictive **Manufacture Innovante Inc.**
- La génération d'un rapport PDF de démonstration dans le conteneur.

## 🛠 Architecture et Sécurité

- **Multi-tenant** : Isolation stricte par `org_id` extraite du JWT (pas de fuite inter-tenant).
- **Pseudonymisation** : Séparation physique des identités et des réponses, hachage rotatif par campagne, et jittering temporel.
- **Report-First** : Génération de PDF haute-fidélité via Playwright (Modèles Direction et CA).
- **Immuabilité** : Snapshot complet de la méthodologie et des données lors de la publication des rapports.

## 🧪 Tests

```bash
# Exécuter la suite complète de tests (SQLite pour la rapidité)
DATABASE_URL=sqlite:///./test.db python -m pytest src/pulse_ia/tests/
```

## 📄 Documentation de Sécurité
Consultez [PRIVACY_RISKS.md](./PRIVACY_RISKS.md) pour le détail des mécanismes de protection des données.
