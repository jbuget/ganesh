# API keys (V1)

> **Built.** This was the design brief; it is now the reference for what
> shipped. The module lives in `server/src/modules/api_keys/`, the screen in
> `client/src/components/organisms/ApiKeysPage.tsx`, and *Out of scope for V1*
> still says what was deliberately left out.

## The gap it closes

Janus authenticates **humans and nobody else**. `get_current_user`
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
| What a key is attached to | A **service account**, never a person |
| What a key can do | Read **and** write, each behind an explicit scope |
| What a key opens by default | **Nothing.** A route opts in, one at a time |
| Who creates and revokes | Managers only |
| Who reads the list | Everyone |
| Expiry | Optional, one year offered in the form |
| Who answers for a key | Its owner, a named human |

### Why no keys bound to a person

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

## A key opens nothing by default

This is the rule the whole design leans on.

- `get_current_user` **refuses API keys outright**. Every route that depends on
  it stays human-only, unchanged, with no audit to rework.
- A new dependency, `require_scope(ApiKeyScope.CATALOG_READ)`, accepts a key and nothing
  else it was not given.
- A route becomes machine-reachable only by asking for it, explicitly, one
  route at a time.

In V1 exactly one route opts in: `export_catalog`. Write scopes exist in the
vocabulary and in the form, but no route accepts them yet — the first one to do
so will be a deliberate act, not a side effect.

A key never inherits its owner's role. `get_current_manager` is unreachable by
a key, because `get_current_user` is.

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
twenty-odd use cases changes shape.

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
  `grep` or a secret scanner, and it tells a Janus key from an Entra token on
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

```
all:read          every read, including ones not invented yet
all:write         every write, same

catalog:read      the service catalogue    ← the only one V1 wires to a route
projects:read
projects:write
entries:read
```

A key with no scope can do nothing — that is a valid, useless key, and the form
does not produce one.

### The two broad ones

`all:read` and `all:write` are **independent, one per verb**: neither covers the
other, and a key that reads and writes everything carries both.

**Writing does not imply reading.** The ladder would have been tidier to write
and worse to hold: a key granted « Tous (écriture) » would have quietly gained
every read, and — the fault that actually showed up in the browser — ticking one
« Tous » after the other trapped the first one checked and unremovable. Two
switches, no implication.

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

## The screen

A new view, `/api`, reachable from the sidebar by everyone.

The sidebar (`client/src/components/organisms/AppSidebar.tsx`) filters nothing
by role, and « API » does not change that: « Utilisateurs » already shows for
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

- **Keys bound to a person.** See *Why no keys bound to a person*.
- **Service accounts as objects of their own.** A key is one, for now.
  Splitting them is what rotation needs.
- **Rotation with an overlap window.** V1 rotation is: create the new one, move
  the consumer over, revoke the old one. Two live keys for one account is V2,
  and it is what would make a mandatory expiry bearable.
- **Rate limiting per key.** Nothing throttles a key. Worth settling before the
  first write scope is wired to a route.
- **IP allowlists.**
- **A true machine actor in the audit.** See *Traceability*.

## Files that matter

| Path | Why |
|---|---|
| `server/src/modules/auth/presentation/dependencies.py` | where `require_scope` goes, beside the Entra path that must keep refusing keys |
| `server/src/modules/auth/presentation/identity.py` | why a machine token is refused today |
| `server/src/modules/users/domain/entities/user.py` | `LOGIN_FRESHNESS`, the pattern `last_used_at` copies |
| `server/src/modules/audit_logs/domain/entities/audit_log.py` | where the two new actions go |
| `server/src/modules/projects/infrastructure/database/models/project_detail_models.py` | `ProjectDepartmentModel`, the shape `api_key_scopes` copies |
| `server/src/modules/projects/presentation/api/routes/project_router.py` | `export_catalog`, the one route that opts in |
| `server/src/modules/entries/presentation/api/routes/entry_router.py` | why there is no per-user data scope to lean on |
| `client/src/components/organisms/AppSidebar.tsx` | the navigation |
| `client/src/components/organisms/UsersPage.tsx` | the closest screen to copy: a table with manager-only actions |
