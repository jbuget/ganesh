@AGENTS.md

# CLAUDE.md — Ganesh

Development guide for Claude Code on this project. These rules apply to every
contribution, without exception.

This project deliberately follows **WAATcher**'s conventions. When in doubt on a
point not covered here, look at what WAATcher does rather than inventing:
**consistency beats personal preference**.

---

## The product

Ganesh lets every developer declare, in days or half days, the time spent (or
planned) on each project or sub-project, as a `days of the month × missions`
grid. It is named after the lord of the *gaṇa* — the troop one belongs to, and
the count: the same root gives *gaṇita*, calculation. He is the scribe who took
down the Mahābhārata on the one condition that the dictation never stop, and the
doorkeeper who turns back whoever has no right to pass. A register kept without
a break, and a door that opens or holds — that is the whole product: Activité
behind, Planification ahead, and a validated month nobody walks into.

**The name is that of a living deity. Keep it sober.** The name, a plain mark,
and one sentence that says why. No mascot, no pun on the trunk, no elephant
winking from an empty state. What would read as a tribute read straight reads as
decoration the moment it is made cute.

**The product is Ganesh; the domain is still a timesheet.** `TimesheetGrid`,
`TimesheetPage` and `useTimesheetMonth` name a monthly time sheet, which is what
they are and what they stay. Only what names the *application* carries the
product's name — what the user reads, the page title, the API's own name. Do not
rename a domain identifier to chase the product: `GaneshGrid` would say nothing
about what it renders.

The database, its user, the Docker volume, the session cookie and the
`localStorage` keys still read `timesheet`, and an API key still announces
itself with `jns_`. Renaming them would cost everyone a fresh database, a new
sign-in and a fresh set of keys, and buy nothing: nobody reads the name of a
volume, and a key prefix is a needle for a secret scanner, not a brand.

- **V1: no Monday integration.** Projects are created in the application or
  imported from CSV.
- **V1.1:** a "Sync to Monday" button, managers only. The `monday_item_id` /
  `monday_subitem_id` columns exist from V1, nullable.
- Monday will **never** be a source of entry: syncing goes one way, Ganesh →
  Monday.

### Roles

| Action | `TEAMMATE` | `MANAGER` |
|---|---|---|
| Fill in one's own month, read and edit a colleague's open month | ✅ | ✅ |
| Create / change a project, change its status | ✅ | ✅ |
| Validate one's own month | ✅ | ✅ |
| Reopen a validated month | ❌ | ✅ |
| Manage teammates | ❌ | ✅ |
| Sync to Monday (V1.1) | ❌ | ✅ |

### Business invariants

These rules are tested **at the domain level**, independently of the API and of
the UI:

- An entry is `0.5` or `1.0`, never anything else.
- **No entry is possible on a non-working day** (weekend or French public
  holiday). The domain carries the rule and the API refuses the write: locking
  the cell on the client is only its reflection.
- A user's entries for one day must not add up to more than `1` (a warning, not
  a block).
- A validated month is **immutable**: no write is possible until a manager
  reopens it.
- Every entry remembers the project status at the moment it is written
  (`status_at_entry`), which makes it possible to measure time spent per phase.
- Off-project work (absences, training, internal) carries no status and is never
  synced.
- A project cut into work packages cannot leave the reference list without
  saying what becomes of them.
- Every action that matters is traced in `audit_log`.

### Leaving the reference list

A mission that is over — delivered, abandoned, or never really started — is
**archived**, and `ProjectStatus` will never grow a phase for it. A phase says
*where the work stands*, archiving says *whether the mission is still one to
book against*: an abandonment is an exit, not a step forward. Writing it as a
phase would erase the one thing worth knowing, which is how far the project got
before it stopped, put a column that steers nothing on a board that steers what
runs, and cost the plan a second exception beside `OPERATIONS`. Nothing is lost
by archiving: entries already booked stay readable, and only the list one can
still book against shrinks.

- **Archiving a project cut into packages says what becomes of them**, in the
  same gesture: they leave with it, or they are detached and carry on as
  projects of their own. Saying nothing is refused — a package left behind
  holds its rank in the plan and its card on the board on behalf of a project
  that has gone. Archiving is therefore a gesture of its own
  (`POST /projects/{id}/archive`), never a field of `PATCH /projects/{id}`.
- **A detached package takes over the axis it was reading.** It was on that
  axis too, under its project's name rather than its own, and coming out blank
  would lose what every screen already showed of it. A project carrying no axis
  hands down none: nothing is invented.
- **Unarchiving brings back one mission, never a tree.** Each package carries
  its own exit date, and the ones that left long before, for their own reasons,
  are not resurrected by their project coming back.
- Telling « stopped » from « delivered, then retired » does not follow from an
  exit date, and deducing it would fabricate a fact nobody recorded. The day a
  screen has to filter on it, record a reason beside `archived_at` — never a
  phase.

---

## Philosophy

This project follows **Software Craftsmanship**: clean, tested, well-architected
code, delivered continuously and with discipline. Every contribution must leave
the code better than it found it (the boy scout rule).

- **TDD**: write the test before the production code. Tests document intent, not
  implementation.
- **Baby steps**: move in small verifiable increments. Every step must compile,
  pass the tests, and leave the code coherent.
- **Clean Code**: explicit names, short single-purpose functions, no pointless
  comments, no dead code.
- **Clean Architecture** (server side): respect the layers — never a dependency
  outwards from the domain.
- **DRY / SOLID**: a business rule is written in one place; API types are never
  written by hand.
- **YAGNI / KISS**: do not anticipate. Implement what was asked, nothing more.

---

## Language: code in English, interface in French

**The whole codebase is in English** — identifiers, comments, docstrings, test
labels, database columns, API fields, enumeration values, URL parameters.

**What the user reads stays in French** — screen labels, phase names in the
timeline, column headings, dialog text, and the CSV import aliases, which accept
the French headers and values the team has been typing.

Three consequences:

- An English comment quoting the interface quotes French. That is right, not an
  oversight.
- A rename must never cross a label. A French label composed at run time —
  `` `${count > 1 ? "mises à jour" : "mise à jour"}` `` — is invisible to the
  type checker and to the tests, which assert on the count and not the wording.
  Only opening the screen catches it. **Check in the browser after any broad
  rename.**
- To find what is still French, do not search with a list of words: it only
  finds what one already has in mind. Extract every identifier, split it into
  words, and read the sorted column of distinct words — what is French stands
  out.

---

## Stack

| Layer | Technology |
|--------|------------|
| Frontend | Next.js 16, TypeScript, React 19, Tailwind CSS 4 |
| BFF | Next.js Route Handlers (`client/src/app/api/`) |
| Backend | Python 3.12, FastAPI, async SQLAlchemy, Alembic |
| Database | PostgreSQL 18 |
| Authentication | Microsoft Entra ID |
| Front-end tests | Vitest + Testing Library |
| Back-end tests | pytest + pytest-asyncio |
| API client | Orval (generated from OpenAPI) |

---

## Server architecture

The backend follows a strict **Clean Architecture** per functional module. Every
module under `server/src/modules/<name>/` is organised in 4 layers:

```
src/modules/<module>/
├── domain/           # Entities, value objects, repository interfaces (no external dependency)
├── application/      # Use cases, DTOs
├── infrastructure/   # SQLAlchemy models, repository implementations
└── presentation/     # FastAPI routes, Pydantic schemas, dependencies
```

Modules: `users`, `projects`, `entries`, `months`, `calendar`, `audit_logs`.

**Golden rules:**
- The domain knows nothing of SQLAlchemy, FastAPI, Pydantic or any framework.
  Entities are `dataclass`es.
- Use cases orchestrate; they do not carry business logic themselves.
- Repositories are interfaces (ABC) in the domain, implemented in the
  infrastructure.
- **A use case may never call another use case.** Extract shared logic into a
  domain service.
- **FastAPI routes never inject a repository directly** — use cases only.
- Always depend on the interface, never on the concrete implementation.

**These rules are not declarative: they are enforced by `import-linter`**
(`server/.importlinter`), run by `make lint` and in CI. A violation breaks the
build.

Shared code (exceptions, generic types) lives in `server/src/shared/`.

---

## Ports and URLs

Default ports. WAATcher occupies `3001-3003` / `8001-8003` / `54321-54323`, so
there is no clash, but any other local service listening on `3000` or `5432`
must be stopped first. The ports can be overridden through `WEB_PORT`,
`API_PORT` and `POSTGRES_PORT` in the root `.env`.

| | Port | URL |
|---|---|---|
| Next.js client | `3000` | http://localhost:3000 |
| FastAPI API | `8000` | http://localhost:8000 |
| PostgreSQL | `5432` | — |

Same conventions as WAATcher: `API_PREFIX=/api/v1`, `AZURE_AD_*` variables,
callback `/api/auth/callback/azure-ad`.

**The BFF exposes exactly the same paths as the API**: the browser calls
`/api/v1/<resource>`, the Route Handler relays to
`${API_URL}/api/v1/<resource>`. One URL vocabulary across the whole project.

### Entra credentials

Ganesh reuses **WAATcher's Entra app registration** (same
`AZURE_AD_TENANT_ID` and `AZURE_AD_CLIENT_ID`). The redirect URI
`http://localhost:3000/api/auth/callback/azure-ad` must therefore be declared on
that app registration in the Azure portal.

The `AZURE_AD_CLIENT_SECRET` lives in `client/.env.local` alone: the BFF is what
carries the OAuth flow. The server only validates tokens and needs nothing but
the tenant and the client id.

---

## Client architecture

- **The BFF is mandatory**: the browser never calls FastAPI directly. It calls
  the Route Handlers under `client/src/app/api/`, which relay to the API,
  injecting the Entra token. The token stays server-side, in an `httpOnly`
  session.
- **Orval hooks only**: data hooks come exclusively from the generated client
  (`client/src/lib/api/generated/`), whose `baseUrl` points at the BFF. Never
  create a custom fetch/axios instance to call the API.
- **No API type written by hand**: they are generated from FastAPI's OpenAPI
  (`pnpm api:generate`).

> **A deliberate divergence from WAATcher.** WAATcher has no BFF: its browser
> calls FastAPI directly through `NEXT_PUBLIC_API_URL`. Ganesh introduces a
> BFF on purpose, so that the Entra token never leaves the server and the API is
> not publicly exposed. That is the one structural gap; everything else follows
> WAATcher.

- **Atomic Design**: see `AGENTS.md`. The composition rules are enforced by
  `eslint-plugin-boundaries`. A violation breaks the lint.

---

## Git

### Branches

**Git Feature Branching** model:

- `main` — production, protected
- `feature/<description>` — new feature
- `fix/<description>` — bug fix
- `chore/<description>` — maintenance, tooling, dependencies
- `refactor/<description>` — refactoring with no functional change

**Workflow:** branch off `main`, open a PR against `main`, merge after review.

**Strict rule:** never push straight to `main`.

### Commits

**Conventional Commits** format, mandatory:

```
<type>(<optional scope>): <short description in English>
```

Types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, `perf`, `ci`

```
feat(entries): capture project status on each timesheet entry
fix(months): prevent writing to a validated month
test(projects): cover status transition rules
```

- Description in English, lowercase, no full stop
- One commit = one clear intent
- No `WIP`, no `fix fix`, no `misc`

Never add a "Co-authored by Claude" line.

### Pull requests

Title and description in French, mandatory template:

```markdown
### Problème

### Solution

### Implémentation

### Recette
```

---

## Quality — mandatory checks before any push

### Backend (`server/`)

```bash
make lint          # isort + black + ruff + flake8 + mypy + import-linter
make test          # pytest with coverage
make format        # fixes isort + black + ruff
make check-schema  # alembic check: the schema matches the models
```

### Frontend (`client/`)

```bash
pnpm lint          # ESLint (Atomic Design rules included)
pnpm format:check  # Prettier
pnpm type-check    # tsc --noEmit
pnpm test          # Vitest
```

From the root: `make check` runs the lot.

**The lint must come out at zero errors at the end of every task**, without
exception.

---

## Tests

### Principles

- **TDD**: red → green → refactor.
- One test = one behaviour, not an implementation.
- No test that tests a mock that tests a mock.
- Use cases are tested with **in-memory repositories**, not mocks.
- Integration tests hit a real database, never a mocked one.
- Backend naming: `test_<what>_<in which context>_<expected result>`.

### Backend — structure

```
server/tests/
├── conftest.py
├── modules/<module>/
│   ├── domain/           # Entities and domain services
│   ├── application/      # Use cases (in-memory repositories)
│   ├── infrastructure/   # Integration, real DB
│   └── presentation/     # FastAPI routes
└── shared/
```

### Frontend — structure

Vitest tests colocated with the source (`*.test.ts` / `*.test.tsx`).

---

## Database migrations

- `Enum` columns are declared `native_enum=False`: SQLAlchemy stores the **name**
  of the Python member, not its value. In the database one therefore reads
  `WORK_PACKAGE`, `OFF_PROJECT` or `SCOPING`, never `work_package` nor
  `scoping`. The ORM translates both ways, but any SQL written by hand must use
  the uppercase names.
- Alembic migrations are **immutable** once applied in production.
- Never change an existing migration without explicit agreement: create a new
  one.
- Automatic naming: `YYYY_MM_DD_<rev>_<slug>.py`
- Every new model must be imported in `server/alembic/env.py`, otherwise
  autogenerate does not see it.
- **A rename carries more than the column.** Renaming a column leaves behind the
  index that carries it, the `NOT NULL` constraint PostgreSQL named after it, and
  any check constraint whose expression names it. `alembic check` sees the index
  and nothing else — the CI runs it, but the constraints must be renamed by
  hand, in the same migration.
- **Renaming an enumeration member rewrites data.** The stored value is the
  member's name: the migration must `UPDATE` every column that carries it, and
  do the reverse on downgrade. The same goes for any key inside a JSON payload,
  such as `audit_log.payload`.

```bash
make migration   # asks for a message
make migrate     # alembic upgrade head
```

---

## Planification and Feuille de route

Two screens read the same missions and answer different questions. Keeping
them apart is what keeps either one worth opening.

**Planification** asks *what fits, and who carries it*. Week by week, over
what is left to build, on the room the diaries leave. It is arbitrated: one
reorders the backlog and puts people on missions to see what that would cost,
and saves the question as a simulation. Services in operations are out of it —
`still_to_build()` drops them — and so is everything already delivered.

**Feuille de route** asks *what we deliver, and when*. Over the whole
portfolio, delivered services included, over a rolling window. It is shown
rather than arbitrated: to a committee, to a department. Where the plan reads
`go_live_date` only to work out a delay, the roadmap makes the announced date
its subject — and is the one place it can be posted.

The window rolls rather than following the calendar, and that is a decision
about where the width of the screen goes. A civil year read in September
spends two thirds of it on a past nobody is deciding anything about;
`rolling_window()` opens one month back and runs `months` ahead, both ends on
month boundaries so the scale draws whole columns. `months` is what the screen
asks with — 3, 6 or 12 — and naming `from_day` and `to_day` instead reads
exactly that window, which is how a year already over is looked back on.

A band folds away the missions that have neither a bar nor a date. They are
counted in plain sight, never dropped: forty of them unfolded drown the dozen
that have something to say, and the count itself is a fact about the
portfolio.

Three rules the drawing rests on:

- **A fact and a supposition are never drawn alike.** Solid is `LIVED`,
  hatched is `PROJECTED`, a thin rule is `RUNNING`. `SegmentKind` decides it in
  the domain, not a colour picked on the front end — colour belongs to the
  phase. Reading a projection as a commitment is the mistake this screen
  exists to prevent. The rule holds down to the red thread: a delay already
  taken is drawn solid, one the projection merely supposes is dashed.
- **Nothing is invented.** What was never recorded leaves no segment, and a
  stretch nobody can date is carried by the nearest phase that is dated. A
  roadmap that fills its own gaps gets read as fact.
- **A placeholder is never counted as a fact.** A running rule has to open
  somewhere to be drawn, and on the missions that were already live before
  anybody recorded a phase, that day is chosen by the drawing — the window's
  edge, which says « since before you started looking ». Only
  `went_live_on` carries the day the register holds, and only it may be read
  by the tally or by an écart. Asking the bar instead makes a portfolio that
  shipped nothing announce « 23 mises en service ».
- **A mission with nothing to draw still shows.** No estimate, no date, no
  time declared — that is the line steering has to see, and the tally above
  says how many there are before anybody reads a bar.

Gestures do not cross: reordering and staffing belong to Planification,
posting a date belongs to the roadmap. Two screens answering the same gesture
end up contradicting each other.

## The service catalogue

waat.tools publishes the services the team produces. Ganesh is the source for
everything it publishes: a mission carries a service sheet, and the « Fiche
service » tab is where that sheet is filled in — nowhere else.

The line between the two tabs of a mission is what one is doing there:
**Pilotage steers the mission, Fiche publishes the service.** Phase, priority,
departments, contributors and cost steer; address, summary, links, stack and
criticality publish. A field belongs to one side or the other, never to both.

- Publishing asks for a slug, a summary, a criticality and a type: what the
  catalogue cannot draw a card without. Off-project work is never published.
- **The catalogue draws one card per service, and a sub-project is not one.** A
  project cut into lots is still one product at one address: a work package is
  published through its project, never beside it. The domain refuses the
  combination, so `GET /projects/catalog` carries no lot by construction.
- **A project joins another from the reference list**, by dragging its row onto
  a project or through the mission menu, which is also the way back out. The
  move carries nothing away: the phase, the estimate and the days booked stay
  on the lot, and the project reads their sum. Only the strategic axis is given
  up, since a lot reads its project's. A published project is refused — it must
  be unpublished first, or its card would leave waat.tools with nobody saying
  so.
- A slug is chosen once and kept: it is a public address, and it must survive
  the mission being renamed.
- `description` is the full sheet in markdown, `summary` the one line a card
  shows. The catalogue reads both, under those two names.
- `make catalog` writes the export; `GET /api/v1/projects/catalog` serves the
  same thing. The shape is described once, in `CatalogEntryResponse`, and it
  speaks camelCase on purpose — it is waat.tools's vocabulary, not ours.

---

## API keys

A machine reaches Ganesh with a key, never with a user account. The rule the
whole design leans on, and the one to respect when adding a route:

- **A key opens nothing by default.** `get_current_user` refuses keys outright,
  so every route that depends on it is human-only. A route becomes
  machine-reachable by asking, with `require_scope(ApiKeyScope.…)` — one route
  at a time, on purpose.
- A key belongs to a **service account**, never to a person, and that account
  carries a **human owner** who answers for it. An API call records the owner
  as the actor and names the key in the payload.
- A key never inherits its owner's role: its power comes from its scopes alone.
- Scopes read `resource:verb`. The two broad ones, `all:read` and `all:write`,
  are independent — one per verb, neither covering the other, and writing never
  implying reading.
- The secret is shown once, at creation, and stored as a SHA-256. There is no
  route that hands it over again.
- A key may only call so often. The bucket is counted **per process**, in
  memory, behind a `RateLimitStore` port — never in the database, which would
  mean a write on every call.

The whole team reads the table of keys; only a manager mints or revokes one.
See `docs/api-keys.md`.

---

## Production

One push to `main` deploys the API. Nothing else deploys it: no laptop builds
the production image, and no one holds a key to the host.

The client is on **AWS Amplify** at `ganesh.waat.tools`, the API on one **EC2
host behind Caddy** at `api.ganesh.waat.tools`, the database on **managed
RDS**. Same shape as NOMAD and SALSA, so that whoever is on call recognises
what they are looking at — and the runbook is `docs/deployment.md`.

Four rules worth knowing before touching `terraform/`, `docker-compose.prod.yml`
or the CD workflow:

- **The host is ARM.** The image is built for `linux/arm64`, and an amd64 one
  pulls without complaint before refusing to start. Never drop the platform
  from the build.
- **No secret goes through Terraform.** The state file is not a vault: the
  parameters are created empty and filled out of band with `put-parameter`.
  Nor does a secret go through the SSM payload, which is logged — the host
  reads Parameter Store itself.
- **The instance and the database carry `prevent_destroy`.** A plan that says
  `replace` on either is a plan to read again, not to apply: the instance holds
  Caddy's certificate store, the database holds everyone's declared months.
- **A deploy ends on the health check.** The API answering is what makes a
  deploy a success, and the migration runs once, inside the container, rather
  than in each worker as it boots.

**The sign-in flow does not exist yet**, so production runs `REQUIRE_AUTH=false`
and the application is open to whoever knows the address. That is a step, not a
state: the day the Entra callback lands in the BFF, the parameter flips and the
next deploy closes the door.

---

## Code conventions

### Python (backend)

- Strict typing everywhere — no `Any` without justification.
- **3.10+ typing syntax is mandatory** — native builtins, never the `typing`
  aliases:

  | Forbidden | Required |
  |-------------|----------------|
  | `Optional[X]` | `X \| None` |
  | `Union[X, Y]` | `X \| Y` |
  | `List[X]` | `list[X]` |
  | `Dict[X, Y]` | `dict[X, Y]` |
  | `Tuple[X, ...]` | `tuple[X, ...]` |
  | `Set[X]` | `set[X]` |
  | `Type[X]` | `type[X]` |

- No business logic in FastAPI routes.
- Business exceptions inherit from
  `src/shared/exceptions/domain_exceptions.py`.
- `async/await` everywhere on I/O — no blocking calls.
- No `print()` in production — use `logging`.

### TypeScript (frontend)

- No `any` — type explicitly or use the types Orval generates.
- Server components by default, `"use client"` only when needed.
- One component = one responsibility. Extract complex hooks into `src/lib/`.
- Every clickable element carries the `cursor-pointer` class.

---

## What must never be done

- Commit `.env` files, secrets or API keys.
- Bypass the commit hooks (`--no-verify`).
- Push straight to `main`.
- Disable a failing test instead of fixing it.
- Work around an `import-linter` contract or a `boundaries` rule instead of
  fixing the design.
- Call FastAPI straight from the browser, going around the BFF.
- Write an API type by hand instead of regenerating the Orval client.
- Leave commented-out code, or `TODO`s with no ticket attached.
