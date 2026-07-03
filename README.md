# Pulse IA - Backend de Pilotage de l'Adoption de l'IA

Pulse IA est une plateforme SaaS permettant de mesurer, analyser et piloter l'adoption de l'Intelligence Artificielle au sein des organisations.

## 🚀 Démarrage Rapide (Démonstration Docker)

Le projet est conçu pour être lancé via Docker Compose pour une reproductibilité totale.

### Prérequis
- Docker et Docker Compose
- `make` (recommandé)

### Lancement de la démo
```bash
# 1. Préparer l'environnement
cp .env.example .env

# 2. Lancer la démo complète (DB + API + Migrations + Seed + Rapports)
make demo
```

Une fois lancé :
- L'API est disponible sur : http://localhost:8000
- La documentation interactive (Swagger) : http://localhost:8000/docs
- **Les rapports PDF générés se trouvent dans le dossier `./artifacts/`**

## 🛠 Commandes de Développement (Makefile)

| Commande | Description |
| :--- | :--- |
| `make setup` | Installe les dépendances Python et Playwright (local) |
| `make up` | Démarre l'infrastructure Docker en arrière-plan |
| `make migrate` | Applique les migrations Alembic |
| `make seed` | Remplit la base avec les données de démo (Idempotent) |
| `make test-unit` | Exécute les tests unitaires rapides (SQLite) |
| `make test-integration` | Exécute les tests sur une instance Postgres éphémère |
| `make clean` | Nettoie les conteneurs, volumes et fichiers temporaires |

## 🧪 Tests et Intégrité

Pour garantir la reproductibilité, les tests d'intégration démarrent leur propre instance PostgreSQL et vérifient l'alignement du schéma Alembic.

```bash
make test-integration
```

## 📄 Architecture et Sécurité
- **Multi-tenant** : Isolation par `org_id` (JWT).
- **Pseudonymisation** : Hachage SHA-256 et jittering temporel.
- **Immuabilité** : Snapshot complet lors de la publication des rapports.
- Consultez [PRIVACY_RISKS.md](./PRIVACY_RISKS.md) pour plus de détails.
