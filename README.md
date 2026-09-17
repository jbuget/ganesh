# Timesheet

Suivi du temps passé par projet pour l'équipe Dev & Automatisation de WAAT.

Chaque développeur déclare, en journées ou demi-journées, le temps passé (ou prévu)
sur chaque projet ou sous-projet, sous forme d'une matrice `jours du mois × missions`.

## Démarrage

```bash
make install     # venv Python + dépendances pnpm
make db-up       # PostgreSQL sur le port du .env
make migrate     # applique les migrations Alembic

make dev-server  # API FastAPI
make dev-client  # Next.js
```

### Ports

`WEB_PORT`, `API_PORT` et `POSTGRES_PORT` sont lus dans le `.env` racine
(`3000` / `8000` / `5432` par défaut) et transmis par les `make` : deux copies du
dépôt tournent côte à côte en changeant ce seul fichier, à condition d'y donner
aussi un `COMPOSE_PROJECT_NAME` distinct. Les URL correspondantes se reportent
dans `server/.env` (`API_URL`, `ALLOWED_ORIGINS`, `DATABASE_URL`) et
`client/.env.local` (`API_URL`, `APP_URL`, `AZURE_AD_REDIRECT_URI`), et l'URI de
redirection doit être déclarée sur l'app registration Entra.

Lancer `pnpm dev` directement depuis `client/` ignore le `.env` racine et
retombe sur `3000` : passer par `make dev-client`.

## Qualité

```bash
make check       # lint + architecture + types + tests, serveur et client
```

## Documentation

- `CLAUDE.md` — charte de développement (architecture, git, tests, conventions)
- `AGENTS.md` — conventions UI et Atomic Design
