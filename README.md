# Timesheet

Suivi du temps passé par projet pour l'équipe Dev & Automatisation de WAAT.

Chaque développeur déclare, en journées ou demi-journées, le temps passé (ou prévu)
sur chaque projet ou sous-projet, sous forme d'une matrice `jours du mois × missions`.

## Démarrage

```bash
make install     # venv Python + dépendances pnpm
make db-up       # PostgreSQL sur le port 5432
make migrate     # applique les migrations Alembic

make dev-server  # API FastAPI  -> http://localhost:8000
make dev-client  # Next.js      -> http://localhost:3000
```

## Qualité

```bash
make check       # lint + architecture + types + tests, serveur et client
```

## Documentation

- `CLAUDE.md` — charte de développement (architecture, git, tests, conventions)
- `AGENTS.md` — conventions UI et Atomic Design
