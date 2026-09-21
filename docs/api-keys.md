# API keys (V1)

> **Built.** This was the design brief; it is now the reference for what
> shipped. The module lives in `server/src/modules/api_keys/`, the screen in
> `client/src/components/organisms/ApiMcpPage.tsx`, and *Out of scope for V1*
> still says what was deliberately left out.

## The gap it closes

Ganesh authenticates **humans and nobody else**. `get_current_user`
(`server/src/modules/auth/presentation/dependencies.py`) validates an Entra
bearer token, pulls an `oid`, an email and a name out of the claims, then
provisions a `User`. A client-credentials token — the kind a CI would obtain —
carries no email, so `identity_from_claims` turns it away with « Token without
an email address ».

Every route under `/api/v1/*` depends on that. The only open endpoint is
`/api/v1/health`.

The first machine that needs in is waat.tools: its build reads
`GET /api/v1/projects/catalog` to publish the service catalogue. Today that
export travels as a file written by `make catalog` and committed by hand,
precisely because there is no way to authenticate the CI.

## Decisions taken

| Question | Decision |
|---|---|
| What a key is attached to | A machine, and the **named human** who answers for it |
| What a key can do | Read **and** write, each behind an explicit scope |
| What a key opens by default | **Nothing.** A route opts in, one at a time |
| Who creates and revokes | Managers only |
| Who reads the list | Everyone |
| Expiry | Optional, one year offered in the form |
| Who answers for a key | Its owner, a named human |

### Why a key never acts *as* a person

**A key is already attached to a person.** `owner_id` is required and points at
`users`; `MachineCaller.actor_id` hands that owner to every use case, so a write
made with a key is traced to a named human. What a key never does is act *as*
that human.

A key acting as a user would be « limited by that user's data scope ». That
scope does not exist. In `entry_router.py` the target is a plain query
parameter:

```python
target_id = user_id or current_user.id
```

Anyone reads and writes anyone's month, deliberately. And `get_current_manager`
guards exactly three routes in the whole product: reopening a validated month,
and the two user-management ones. A key « as Jérémy » would therefore be
limited by nothing, while doubling the model. Revisit the day a real per-user
data scope exists.

So the rule to hold is not « never a person ». It is: **a key carries a human
who answers for it, and never that human's role.** One key per teammate — a
terminal client reaching Ganesh on their behalf — breaks nothing here, and the
audit reads better for it than a shared key would.

## A key opens nothing by default

This is the rule the whole design leans on.

- `get_current_user` **refuses API keys outright**. Every route that depends on
  it stays human-only, unchanged, with no audit to rework.
- A route becomes machine-reachable only by asking for it, explicitly, one
  route at a time.

A key never inherits its owner's role. `get_current_manager` is unreachable by
a key, because `get_current_user` is.

### Two doors, and when each is right

`require_scope(scope)` opens a route to a machine **and to nobody else**. That
is right for the catalogue export: no screen calls it, and the team has no
business there.

`open_to_machines(scope)` **adds** a door to a route the team already comes
through. Whoever signed in keeps coming in exactly as before; a key gains a way
in beside them. Every scope but `catalog:read` is wired this way, because every
other route a machine wants is one a screen already reads.

The header decides which door, once, on the `jns_` prefix — the same reading
`get_current_user` does to turn a key away. A key that is refused is **not**
tried again as though a person had called.

`get_current_user` is called rather than declared inside that door. FastAPI
resolves every declared dependency, so a key would be refused by the human door
before the machine one was ever consulted. `teammate_or_machine` is the wrapper
that makes the difference, and it is a dependency in its own right so that a
test can stand a teammate at the door without standing the door down.

What a route gets back is a `Caller`: an `actor_id` either way, and the key
when a machine called. A write records an actor whoever knocked; a read ignores
it, as it already ignored the user.

## Service accounts

**In V1 a key *is* a service account.** One table, one row per machine:
`name` + `owner` + scopes. Splitting the account from its keys is what
rotation needs, and rotation is V2 — see *Out of scope*.

**The owner is a human, and it is required.** Someone answers for what a
machine does; a credential nobody owns is the one nobody reviews and nobody
revokes. The owner is who to warn before an expiry and who to ask when a key
turns up in a log.

**A key whose owner is deactivated stops working.** A key is only as alive as
the person answering for it. This is also the offboarding story: deactivating
someone cuts their machines with them.

**A service account carries no role.** Its power comes from its scopes and from
nothing else. There is no such thing as a manager service account.

## Traceability

Write access is the reason this matters. `audit_log.actor_id` is a foreign key
to `users`, and every use case takes an `actor_id: int`.

A call made with a key records **its owner** as the actor, and names the key in
the payload:

```python
payload = {"field": "…", "api_key": "jns_ab12cd34ef56"}
```

The trace says both *what* did it and *who answers for it*, and not one of the
twenty-odd use cases changes shape. That promise is now kept by a decorator,
`MachineStampedAuditLog`: `get_audit_log_repository` wraps the plain repository
when the request carries one of our tokens, and every line written through it
names the key. What writes the log never learns what a machine is.

**The key is read from the public half of the token alone** — no lookup, no
hash, no authentication — and that is not a shortcut. A line is only ever
written on a route that opened its own machine door and checked the key there;
a forged token never reaches a use case. What is stamped is a lookup handle,
which is not a secret and is exactly what the table of keys already shows.

> **The V2 that reads better.** A true machine actor — `actor_id` nullable, a
> new `api_key_id` column on `audit_log`, an `Actor` value object replacing
> `actor_id: int` everywhere — says « the CI did this » without leaning on a
> human. It is a mechanical refactor across those twenty use cases, their
> commands, their routes and their tests. The model above upgrades into it
> without a data migration: the payload already carries the key.

## The key itself

### Shape

```
jns_<public_id>_<secret>
     12 chars    43 chars
```

- `jns_` — a distinctive prefix. It makes the key recognisable in a log, a
  `grep` or a secret scanner, and it tells a Ganesh key from an Entra token on
  the same header.
- `public_id` — random, unique, **indexed**, not secret. It is the handle the
  lookup goes through, and the only part of the key ever shown again.
- `secret` — 43 characters drawn from letters and digits, ~256 bits. Never
  stored. Not `token_urlsafe`: its alphabet holds `_`, the very character the
  three parts are split on.

### Storage

Store `sha256(secret)`, hex, and nothing else.

**Not bcrypt or argon2.** Those exist to slow down a dictionary attack on a
password a human chose. The secret here is 256 bits of randomness: there is no
dictionary, and no amount of hashing rounds changes that. What they would buy
is ~100 ms of CPU on every single API call.

**No pepper either**, for the same reason: a stolen database gives an attacker
a SHA-256 of 32 random bytes, which is not reversible. A pepper would add an
environment variable whose loss invalidates every key, for no gain against this
threat. Revisit only if the hash ever protects something with less entropy.

### Verification

1. Split on `_`, keep `public_id` and `secret`.
2. Look the key up by `public_id` — one indexed row, never a scan over hashes.
3. `hmac.compare_digest(sha256(secret), row.secret_hash)`. Constant time, so a
   wrong key cannot be narrowed down by timing.
4. Check the state: revoked, expired, or owner deactivated → refused.
5. Check the scope the route asks for.

### Transport

`Authorization: Bearer jns_…`, the same header as an Entra token. The auth
dependency tells them apart by the `jns_` prefix. One header, one standard
scheme, nothing new for a client to learn — GitHub does exactly this with
`ghp_` tokens alongside OAuth.

## Scopes

A closed enumeration, `resource:verb`. Each member names what a route needs,
not what a screen shows.

**Every scope listed opens at least one door.** That is not a remark, it is a
test — `test_every_scope_the_form_offers_opens_a_door` walks what the doors
registered at import time and fails on a member nothing asks for. A door, not
a route: a **tool** opens one too, through `@answers` (see `docs/mcp.md`), and
two scopes are opened by a tool alone. The first
round shipped four scopes of which one was wired; the table of keys said what a
key opened and said it wrong, and a key minted on « Projets (écriture) » opened
nothing at all. A promise the API does not keep is worse than a missing box.

| Scope | What it opens | What it deliberately does not |
|---|---|---|
| `catalog:read` | `GET /projects/catalog` — machine-only | — |
| `roadmap:read` | `GET /planning/roadmap` | the projection and the simulations: an arbitration, not a reading |
| `stats:read` | `GET /stats` | — |
| `projects:read` | `GET /projects`, `/projects/{id}/detail`, `/projects/board`, the `find_project` and `project_brief` tools | — |
| `projects:write` | create, correct, change phase, archive, unarchive, import | delete, attach/detach, staff, move a card, and the whole service sheet |
| `updates:write` | `POST /projects/{id}/updates` | correcting and removing a post |
| `entries:read` | `GET /entries/export` | writing time through a route |
| `entries:write` | the `declare_time` tool, and no route | writing anybody else's month |
| `users:read` | `GET /users` | role, activation, identity |
| `audit:read` | `GET /audit-logs` | — there is nothing to write |
| `moods:read` | the `team_mood` tool, and no route | every name, and what anyone answered |

### Why those, and not the others

- **The roadmap, not the plan.** The roadmap is the screen that is *shown* —
  to a committee, to a department — so a build that publishes it outside
  Ganesh is doing what it is for. Planification is arbitrated: one reorders a
  backlog and puts people on missions to see what it would cost. A machine has
  no question to put.
- **Reading the directory, never writing it.** A role and an activation are a
  manager's gestures, and a key carries no role. `users:write` would hand a
  machine the very power the design refuses it.
- **Writing the reference list, not restructuring it.** Creating, correcting
  and importing are a reprise of data — the CSV import is already that
  gesture, done by hand. Deleting, attaching and staffing restructure; a
  card's rank steers nothing and is not even in the log.
- **The service sheet stays human.** It is filled in Ganesh and nowhere else,
  which is exactly why waat.tools *reads* the catalogue rather than writing it.
- **Time is written by a tool, and by no route.** The rules a write runs into
  — a validated month, a day that is not a working one, a value the grid does
  not hold — are rules a person is told about on screen and argues with, and a
  machine would only ever be told « 422 ». A tool can say them, which a route
  cannot: `declare_time` names each one in French, and writes on the month of
  the key's owner and no other. `PUT /entries` stays human, where a teammate
  may still fix a colleague's month.
- **The moods are reached by one tool, in aggregate, and by nothing else.**
  They are given in confidence, and what would break that is not reading them
  — the team screen names everyone — but aggregating *one person over time*,
  which a model handed the names would do at once. `team_mood` returns no
  name, no initials and no identifier, and says so rather than averaging a day
  too few people answered.

  `moods:read` is also the one scope **no breadth covers**: `NEVER_BROAD` in
  the domain keeps `all:read` from reaching it, and the form neither ticks nor
  locks its box. Reaching the moods is a decision somebody took, on a key the
  whole team can read off the table — never something a key inherited by being
  broad.

**A key must carry at least one scope**, and that is enforced rather than
merely unoffered: `ApiKey.__post_init__` refuses an empty list, and
`CreateApiKeyRequest` declares `Field(min_length=1)`. A key that opens nothing
is a credential somebody has to reason about later for no reason at all.

### The two broad ones

`all:read` and `all:write` are **independent, one per verb**: neither covers the
other, and a key that reads and writes everything carries both.

**Writing does not imply reading.** The ladder would have been tidier to write
and worse to hold: a key granted « Tous (écriture) » would have quietly gained
every read, and — the fault that actually showed up in the browser — ticking one
« Tous » after the other trapped the first one checked and unremovable. Two
switches, no implication.

**A broad scope covers what a route opens to machines, never what the API
knows.** The distinction was not worth writing down while everything the
product held was fair game; it is now, because the moods are deliberately shut.
A resource stays shut by no route opting in, and `all:read` cannot talk it
open. What the two do carry is every scope **added later** — that is the price
of breadth, and the reason the form says so where the box is ticked.

> **This reverses what an earlier draft of this document said**, which was
> « grow it by adding a member, never by inventing a wildcard ». The reversal is
> deliberate and it has a price: a broad scope covers routes that **do not exist
> yet**, so a key minted today gains whatever is added tomorrow. Two things keep
> that honest — they are real enum members, so a key can still be read off the
> table and told what it opens, and the form says as much where the box is
> ticked.

The form ticks and **locks** what a broad scope carries, naming where each
locked box gets its right from. Only what is not covered is sent: the server
derives the rest from `ApiKey.grants`, and a stored list of redundant scopes
would only make the table harder to read.

The picker sets the two apart, above a rule. They are a different kind of
decision from the nine beneath them — a reach granted once and for all,
including over what does not exist yet — and reading them as the first two
items of one long list is what gets them ticked by accident.

## Two routes that had to exist first

Two scopes named a resource the API held and had no way to hand over. Wiring
them to what existed would have produced a scope that was technically true and
practically useless, which is the same fault in a different coat.

**`GET /entries/export?from_day=&to_day=`** — every entry of a window, whoever
declared it, on whatever mission, each row carrying the names that make it
readable beside the ids that make two pulls reconcilable. The grid answers one
person's question — my month — and looping over it would have made a caller
redo the join N people by M months. Capped at a year and a day: a guard on a
route a machine calls, not a business rule.

Declared **on** the window, not declared *during* it. A day entered late comes
out under the day it is about, which is what a register is for — and why the
same window pulled twice can differ.

**`GET /audit-logs?limit=&offset=&since=`** — the whole log, most recent first.
A mission's « Journal » tab answers « what happened to this project »; this
answers « what happened », which is the question an archive puts and one no
screen puts. `since` is what makes an incremental pull possible: a reader
holding everything up to a moment asks for what came after, rather than paging
back through a log that only grows.

## Who sees what

The whole team reads the list of keys. Only a manager creates or revokes one.

**The list carries no secret, by construction.** `public_id` is the lookup
handle, not a piece of the credential: knowing it helps nobody forge a key.
That is what makes the table safe to show, rather than any amount of trust —
and it is the rule to hold on to:

> The listing never shows anything that helps anyone **use** a key.

Any future column has to pass that test before it is added.

Showing it is not a concession, it is a safeguard. A key nobody looks at is a
key nobody notices has been idle for eight months, or is carrying
`projects:write` for no reason. Opening the table puts eyes on it — the same
reasoning the audit log already states: freedom of action only makes sense if
every move leaves a readable trace.

Two consequences:

- **The server refuses creation and revocation to a non-manager whatever
  happens.** A hidden button is a convenience, never the rule.
- A teammate sees the table without a « Créer une clé » button, and the empty
  state says « Aucune clé » rather than inviting an action they cannot take.

And one that reaches into the form: since strangers read the table, the
**name** of a key is an interface contract. « CI waat-tools » tells them
something; « clé test » tells nobody but its author.

## Data model

A new module, `server/src/modules/api_keys/`, in the four layers the others
follow. **`users` is not touched** — a service account is not a user, and
keeping it out of that table is what spares the eight places that call
`users.list_all()` (the board, the project detail and list, the catalogue
export, the workload plan, the statistics, the admin screen, the update
thread). A service account listed among teammates would be planned four and a
half days a week and counted in the team size.

**`api_keys`**

| Column | Notes |
|---|---|
| `id` | |
| `name` | The machine it serves: « CI waat-tools ». Required, and read by the whole team. |
| `public_id` | Unique, indexed. The lookup handle. |
| `secret_hash` | |
| `owner_id` | FK `users`, `RESTRICT`. The human who answers for it. Required. |
| `created_by` | FK `users`, `RESTRICT`. Who minted it — a manager, not always the owner. |
| `created_at` | |
| `expires_at` | Nullable |
| `last_used_at` | Nullable |
| `revoked_at`, `revoked_by` | Nullable. The row stays: a revoked key must still be readable in the audit. |

**`api_key_scopes`** — `(api_key_id, scope)`, on the model of
`project_departments`.

### `last_used_at`

Write it through a freshness window, exactly as `User.last_login_at` already
does (`LOGIN_FRESHNESS`, 15 minutes, in
`server/src/modules/users/domain/entities/user.py`). Without it the column
measures HTTP traffic and writes a row on every request.

It is the column that makes revocation safe: a key nobody has used in six
months is a key one can cut without asking around. Since the whole team reads
the table, it is also the column that lets anyone raise the question.

## API surface

```
GET    /api/v1/api-keys          list, any signed-in teammate
POST   /api/v1/api-keys          create, managers only — returns the secret ONCE
PATCH  /api/v1/api-keys/{id}     correct the name and the scopes, managers only
DELETE /api/v1/api-keys/{id}     revoke, managers only
```

`PATCH` carries **the name and the scopes, and nothing else**. The secret is
not reissued, the owner is not swapped, the expiry is not moved: those are
reasons to mint a new key, not to bend an old one. A field left out is a field
left alone.

**A revoked key is frozen.** It says what a machine was called while it
worked, and the audit refers to that — rewriting it afterwards would rewrite
the trace. An expired key may still be renamed: pointless for the machine,
useful for whoever reads the table.

These three are human routes: they depend on `get_current_user`, so a key can
never manage keys.

The listing never returns a secret, only `jns_<public_id>`. `POST` is the one
and only response that carries the whole key.

Audit: three new `AuditAction` members — `API_KEY_CREATE`, `API_KEY_UPDATE`
and `API_KEY_REVOKE`. A correction traces one line per field that changed.

### Status codes

- `401` — unknown, malformed, expired, revoked, or owner deactivated. **One
  answer for all five.** Telling an expired key from an unknown one hands an
  attacker a way to enumerate.
- `403` — the key is valid but lacks the scope the route asks for. Here the
  distinction is useful: the caller holds a real key and needs to know what to
  ask for.

### Two things never to do

- **Never log the `Authorization` header**, in any handler or middleware.
- **Never return a secret twice.** There is no « reveal » endpoint, because
  there is nothing left to reveal.

## How often a key may call

A leaked key is not only read by whoever should not have it: it is read
*fast*. A limit is what turns a leak into a nuisance rather than an outage,
and what keeps a looping script from taking the API down for everyone else.

**A token bucket, not a fixed window.** A window lets a caller fire its whole
allowance at the end of one and again at the start of the next — twice the
limit at the very moment it matters. A bucket refills steadily, so a burst is
bounded by what has actually accrued.

**A refused call spends nothing.** Hammering a closed door does not hold it
shut for longer: that is the difference between a limit and a punishment.

**Only a key that has proved itself is counted.** The limit guards against a
caller holding a real key; turning away a forged one costs a hash and must not
eat anyone's allowance.

Every answer **to a key that has proved itself** carries `X-RateLimit-Limit`
and `X-RateLimit-Remaining` — a caller should be able to slow down before being
told to — and a `429` adds `Retry-After`, rounded up, because « wait 0 s »
invites an instant retry. A `401` and a `403` carry neither, which follows from
the rule just above: the bucket is only consulted once the key is known.

```
API_KEY_RATE_ALLOWANCE=120       # calls
API_KEY_RATE_WINDOW_SECONDS=60   # over this long
```

> **The counters live in the memory of the process.** Behind several workers
> the effective allowance is multiplied by their number, and a restart hands
> everyone a full bucket. Both are accepted for now, and both are why this
> sits behind a `RateLimitStore` port: moving the counters to Redis changes
> one file.
>
> Counting in the database was turned down on purpose — it would mean a write
> on every single call, which is exactly the amplification that was taken off
> the authentication path.

Not per key: one allowance for all of them. A CI that legitimately needs more
than a script is a reason to add a column, and a reason to have the UI say so.

## The screen

A new view, `/api-mcp`, reachable from the sidebar by everyone, where it
reads « API / MCP ». The path is not `/api`: under Next.js that belongs to the
BFF. Two tabs: « API » carries the table of keys, « MCP » says how a terminal
client branches onto the server with one — see `docs/mcp.md`.

The sidebar (`client/src/components/organisms/AppSidebar.tsx`) filters nothing
by role, and « API / MCP » does not change that: « Utilisateurs » already shows for
the whole team though managing teammates is a manager's job. One rule for the
navigation — it shows what exists — and the permission lives on the actions.

**The list** — name, `jns_ab12cd34ef56`, scopes, owner, who created it and
when, last used, expiry, state (active / expired / revoked). Sorted with the
usable ones first; revoked ones stay, dimmed. Read by everyone.

**Creating** — managers only. A dialog asking a name, an owner, scopes, and an
expiry with one year offered. The name is written for whoever will read the
table next, not for its author: the field says so. On success the whole key
appears **once**, in a panel that says so unambiguously, with a copy button.
Closing it is final. That panel is the single most important screen of the
feature: everything else is recoverable, this is not.

**Opening one** — the whole row opens a panel beside the list, as a teammate's
does. The name is corrected in the header, under the pencil; the scopes just
below. Both are a manager's, and a teammate reads the same panel without a box
to tick.

**Revoking** — managers only, from the panel. A confirmation naming the key,
and a sentence saying that whatever uses it will stop working. Immediate and
irreversible.

**Empty state** — for a manager, say what a key is for before showing the
button. For everyone else, « Aucune clé » and nothing to click.

## Out of scope for V1

Named so nobody wonders whether they were forgotten:

- **A key inheriting its owner's role or data scope.** See *Why a key never
  acts as a person*.
- **Service accounts as objects of their own.** A key is one, for now.
  Splitting them is what rotation needs.
- **Rotation with an overlap window.** V1 rotation is: create the new one, move
  the consumer over, revoke the old one. Two live keys for one account is V2,
  and it is what would make a mandatory expiry bearable.
- **IP allowlists.**
- **A true machine actor in the audit.** See *Traceability*. The payload names
  the key today, which is what makes that upgrade a refactor rather than a data
  migration.
- **Writing time through a route.** A tool writes it — see *Why those, and not
  the others* — and `PUT /entries` stays human.
- **A per-key allowance.** One bucket for all of them, still. A CI that
  legitimately needs more than a script is a reason to add a column.

## Files that matter

| Path | Why |
|---|---|
| `server/src/modules/api_keys/presentation/dependencies.py` | both doors, the `Caller` they hand over, and `OPENED_SCOPES` |
| `server/src/modules/auth/presentation/dependencies.py` | the Entra path that must keep refusing keys |
| `server/src/modules/auth/presentation/identity.py` | why a machine token is refused there |
| `server/src/modules/users/domain/entities/user.py` | `LOGIN_FRESHNESS`, the pattern `last_used_at` copies |
| `server/src/modules/audit_logs/infrastructure/machine_stamped_repository.py` | how a line comes to name the key that wrote it |
| `server/src/modules/entries/presentation/dependencies.py` | where that decorator is put on, and why it needs no lookup |
| `server/src/modules/projects/presentation/api/routes/project_router.py` | the four doors of the reference list, and what each leaves alone |
| `server/tests/modules/api_keys/presentation/test_open_to_machines.py` | the door under test, and the scope that must open a route |
| `client/src/lib/api-keys.ts` | what the form offers, and the test that keeps it level with the API |
| `client/src/components/molecules/ScopePicker.tsx` | the broad two set apart, above a rule |
