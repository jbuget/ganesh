# Ganesh

Per-project time tracking for WAAT's Dev & Automation team.

Every developer declares, in days or half days, the time spent (or planned) on
each project or sub-project, as a `days of the month × missions` grid.

## Getting started

```bash
make install     # Python venv + pnpm dependencies
make db-up       # PostgreSQL on the port from .env
make storage-up  # MinIO, where the files a project carries are put down
make migrate     # applies the Alembic migrations

make dev-server  # FastAPI API
make dev-client  # Next.js
```

## The service catalogue

A mission carries a service sheet — public address, summary, links, stack,
criticality — filled in under the « Fiche service » tab. Publishing it puts the
service in **waat.tools**, the internal catalogue.

```bash
make catalog OUT=../waat-tools/content/catalog.json
```

The same content is served by `GET /api/v1/projects/catalog`, which is where
waat.tools will read it once Ganesh is deployed. Until then the file is written
here and committed over there: same contract, other pipe.

Only published missions leave, and publishing asks for an address, a summary, a
criticality and a type — what the catalogue cannot draw a card without.

### Ports

`WEB_PORT`, `API_PORT`, `POSTGRES_PORT` and `MINIO_PORT` are read from the
root `.env` (`3000` / `8000` / `5432` / `9000` by default) and passed on by the `make` targets: two
copies of the repository run side by side by changing that one file, provided it
also carries a distinct `COMPOSE_PROJECT_NAME`. The matching URLs go into
`server/.env` (`API_URL`, `ALLOWED_ORIGINS`, `DATABASE_URL`) and
`client/.env.local` (`API_URL`, `APP_URL`, `AZURE_AD_REDIRECT_URI`), and the
redirect URI must be declared on the Entra app registration.

Running `pnpm dev` straight from `client/` ignores the root `.env` and falls
back to `3000`: go through `make dev-client`.

## Production

`ganesh.waat.tools` is served by AWS Amplify, `api.ganesh.waat.tools` by one
EC2 host behind Caddy, and the database is managed RDS. A push to `main`
deploys the API through GitHub Actions and SSM — no SSH key, no port 22.

The infrastructure is in `terraform/`, the runbook in `docs/deployment.md`.

## Quality

```bash
make check       # lint + architecture + types + tests, server and client
```

## Documentation

- `CLAUDE.md` — development charter (architecture, git, tests, conventions)
- `AGENTS.md` — UI conventions and Atomic Design
- `docs/deployment.md` — deploying to AWS, and running it once it is there
