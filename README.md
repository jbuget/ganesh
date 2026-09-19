# Janus

Per-project time tracking for WAAT's Dev & Automation team.

Every developer declares, in days or half days, the time spent (or planned) on
each project or sub-project, as a `days of the month × missions` grid.

## Getting started

```bash
make install     # Python venv + pnpm dependencies
make db-up       # PostgreSQL on the port from .env
make migrate     # applies the Alembic migrations

make dev-server  # FastAPI API
make dev-client  # Next.js
```

### Ports

`WEB_PORT`, `API_PORT` and `POSTGRES_PORT` are read from the root `.env`
(`3000` / `8000` / `5432` by default) and passed on by the `make` targets: two
copies of the repository run side by side by changing that one file, provided it
also carries a distinct `COMPOSE_PROJECT_NAME`. The matching URLs go into
`server/.env` (`API_URL`, `ALLOWED_ORIGINS`, `DATABASE_URL`) and
`client/.env.local` (`API_URL`, `APP_URL`, `AZURE_AD_REDIRECT_URI`), and the
redirect URI must be declared on the Entra app registration.

Running `pnpm dev` straight from `client/` ignores the root `.env` and falls
back to `3000`: go through `make dev-client`.

## Quality

```bash
make check       # lint + architecture + types + tests, server and client
```

## Documentation

- `CLAUDE.md` — development charter (architecture, git, tests, conventions)
- `AGENTS.md` — UI conventions and Atomic Design
