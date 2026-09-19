# Janus — client

Next.js front end and BFF. See the [root README](../README.md) to get started,
`AGENTS.md` for the UI conventions and `CLAUDE.md` for the development charter.

Start the client through `make dev-client` from the root, never with `pnpm dev`
from here: run straight from this directory, Next ignores the root `.env` and
falls back to port `3000`, which is not necessarily the one the API and the
Entra redirect URI were configured for.

Useful commands, from this directory:

```bash
pnpm lint          # ESLint, Atomic Design rules included
pnpm format:check  # Prettier
pnpm type-check    # tsc --noEmit
pnpm test          # Vitest
pnpm api:generate  # regenerates the Orval client from the API's OpenAPI
```
