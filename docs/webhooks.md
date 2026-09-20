# Webhooks (V1)

> **Design brief.** Nothing of this is built yet. It says what should be, and
> why each fork was taken the way it was. *Out of scope for V1* is part of the
> proposal, not an afterthought.

## The gap it closes

Ganesh knows things nobody else knows in time. A month is validated on the 3rd
and the person who chases the stragglers finds out by opening the screen. A
project moves from `BUILD` to `LIVE` and the committee hears about it at the
next committee. A service sheet is published and waat.tools keeps serving the
card it was built with, until somebody thinks to rebuild it.

Every one of those facts is already **recorded, named and timestamped** in
`audit_log`. What is missing is the door outwards: a way for Slack, for
waat.tools's build, for an n8n scenario, to be told rather than to poll.

API keys opened the door inwards — a machine can now read Ganesh. Webhooks are
the same door in the other direction, and they deliberately reuse its grammar:
a named subscription, a human who answers for it, a secret shown once, minted
by a manager and read by the whole team.

## Decisions taken

| Question | Decision |
|---|---|
| Where events come from | The **audit log**. A gesture that leaves no line leaves no event |
| What an event is | A fact announced outwards, past tense — `month.validated` |
| Granularity | **One gesture, one event.** A PATCH touching five fields sends one |
| Who creates and revokes a subscription | Managers only |
| Who reads the list | Everyone, as for API keys |
| Transport | `POST` of JSON over HTTPS, signed HMAC-SHA256 |
| Delivery guarantee | **At least once**, with a stable delivery id for deduplication |
| On failure | Exponential backoff, six attempts, then the subscription suspends |
| Where the queue lives | PostgreSQL, written in the gesture's own transaction |
| Filtering | By event, and by nothing else in V1 |

---

## The catalogue of events

### The rule that decides what is in it

**An event is a gesture someone outside Ganesh would act on.** That is the
whole filter, and it explains every absence below.

`entry.set` fires forty times while one person fills a Tuesday afternoon. It is
exactly what the audit log is for and exactly what a webhook is not: nobody
downstream does anything on the news that half a day moved from one project to
another. What they act on is the month being *closed*.

### Why the names differ from the audit actions

An audit line names a gesture from the inside — `month.validate`, read as
« Jérémy **a validé** ». An event announces a fact to a stranger —
`month.validated`, read as « a month **has been** validated ». Same fact, two
readers.

The two sets could not be made identical anyway: three of the events worth
sending do not exist as an `AuditAction` today (see below), and one audit
action covers several events (`project.update` carries publication, archiving
and attachment alike). The mapping is therefore explicit, written in one place,
and under test.

### Months and time entered

| Event | When | Carries | Who waits for it |
|---|---|---|---|
| `month.validated` | A teammate closes their own month | user, month, total days, split by project | Slack #compta, the monthly export, an invoicing scenario |
| `month.reopened` | A manager reopens a validated month | user, month, manager | The same reader, who must undo what they did |

`entry.set`, `entry.clear`, `month.project_add` and `month.project_remove` stay
**inside**. Volume, and nothing downstream acts on them.

### Projects

| Event | When | Carries | Who waits for it |
|---|---|---|---|
| `project.created` | A project enters the reference list | project, kind, axis, creator | Slack #projets, a Monday sync (V1.1) |
| `project.updated` | Any field of Pilotage or Fiche moves | project, `changes[]` with before/after | An audit trail outside Ganesh |
| `project.status_changed` | The phase moves | project, `from`, `to` | Slack, the roadmap seen from elsewhere |
| `project.published` | The service sheet goes live | project, slug, summary, criticality | **waat.tools's build** — the one that rebuilds the catalogue |
| `project.unpublished` | The card must leave waat.tools | project, slug | Same, and it is the urgent half |
| `project.archived` | The mission leaves the reference list | project, what became of its packages | Cleanup of whatever mirrors the list |
| `project.unarchived` | It comes back, alone | project | Same |
| `project.attached` | A project becomes a package of another | project, new parent | Whatever draws the tree |
| `project.detached` | It comes back out | project, former parent, axis taken over | Same |
| `project.deleted` | The line is gone | project id, name | Cleanup |
| `project.assigned` | A contributor is declared | project, member, role | Staffing, a Slack channel invitation |
| `project.unassigned` | They are no longer expected | project, member, role | Same |
| `project.went_live` | `went_live_on` is recorded | project, the day | The tally of what actually shipped |

`project.went_live` is worth its own event rather than being read off
`project.updated`: the roadmap already insists that the day a service went live
is a **recorded fact**, never a bar's starting edge. Whoever counts « mises en
service » must count this and nothing else.

`project.published` likewise. Today publication is a field of the project and
the audit writes it as `project.update` with `{"field": "is_published"}` — a
consumer would have to know that to catch it. The event exists to stop
waat.tools's build from having to read our field names.

### Updates posted on a project

| Event | When | Carries |
|---|---|---|
| `update.posted` | A mise à jour is published on a project | project, author, body, posted date |
| `update.edited` | It is corrected | project, author, body |
| `update.removed` | It is withdrawn | project, author |

This is the one whose Slack relay pays for itself on day one.

### Teammates

| Event | When | Carries |
|---|---|---|
| `user.created` | Somebody arrives | user, email, role |
| `user.role_changed` | Teammate ↔ manager | user, from, to |
| `user.deactivated` / `user.activated` | They leave, or come back | user |

An onboarding scenario reads the first, a licence audit reads the rest.

### Keys and subscriptions

| Event | When |
|---|---|
| `api_key.created` | A key is minted |
| `api_key.revoked` | A key is cut |

Both point at a private channel, never the team one. `api_key.updated` is not
sent: renaming a key is not a security fact.

**`webhook.*` is never an event.** A subscription that could report on
subscriptions would report on its own suspension and feed itself. The audit log
records those gestures; the door does not open on itself.

### What is deliberately outside, and stays outside

- **Moods.** They are given in confidence. The product already refuses to log
  who felt what; posting it to a Slack channel would be worse than logging it.
  There is no event, and adding one is a decision to argue for, not a gap.
- **Sign-ins.** Stamped on `last_login_at` and nowhere else, by the same
  reasoning as the audit log.
- **The rank of a card in a kanban column.** It decides nothing and would
  drown every channel it reached.
- **Individual time entries.** Volume, and no reader.
- **Simulations** (`simulation.*`). They are questions asked on the plan, not
  facts about the portfolio. Revisit the day a simulation is shared outside.

### Temporal events, and why they are not in V1

« Nobody has validated their October » is not a gesture: it is the **absence**
of one, noticed on a date. Same for a key about to expire. Those need a
scheduler — a thing the deployment does not have, the API being one container
with one process and no cron beside it.

They are the natural second act (`month.unvalidated`, `api_key.expiring`,
`project.go_live_overdue`), and the design below leaves room: an event whose
`actor` is null is an event nobody caused. But shipping them means answering
« where does the clock run », and that is its own decision.

---

## What a subscription is

| Field | Read as |
|---|---|
| Name | « Slack #projets », « Build waat.tools ». The whole team reads it |
| URL | HTTPS, public. Fixed at creation, changed only by recreating |
| Events | An explicit list. `*` is refused — a subscription says what it wants |
| Owner | The human who answers for what this endpoint does with the data |
| Secret | Shown once, at creation. Rotatable. Never handed back |
| State | Active, suspended (with a reason), or revoked |

A subscription carries the same three facts a key does — who it serves, who
answers for it, what it opens — because the person reading the table is the
same person, and two tables that read alike must not drift apart.

**A suspended subscription is not a revoked one.** Suspension is Ganesh's
verdict on an endpoint that stopped answering; it is reversible from the
screen, and it says why and since when. Revocation is a decision, and it is
final.

---

## The delivery contract

### The request

```http
POST /whatever-the-subscriber-asked-for HTTP/1.1
Content-Type: application/json
User-Agent: Ganesh-Webhook/1
X-Ganesh-Event: month.validated
X-Ganesh-Delivery: 5a0e8c9e-3c29-4a4e-9f0e-bd0a2f8e1c77
X-Ganesh-Timestamp: 1758361931
X-Ganesh-Attempt: 1
X-Ganesh-Signature: sha256=8f4a…
```

- `X-Ganesh-Delivery` is **stable across retries**. It is what the consumer
  deduplicates on, and the reason at-least-once is an honest promise rather
  than a shrug.
- `X-Ganesh-Attempt` starts at 1. A consumer that logs it can see its own
  outages.

### The signature

```
signature = HMAC-SHA256(secret, f"{timestamp}.{raw_body}")
```

The timestamp is inside the signed material, so a captured call cannot be
replayed a week later; the consumer is told to refuse anything older than five
minutes. The body is signed **raw**, before any parsing: a consumer that
re-serialises before verifying will get it wrong, and the documentation says so
in as many words.

### The payload

```json
{
  "id": "5a0e8c9e-3c29-4a4e-9f0e-bd0a2f8e1c77",
  "event": "month.validated",
  "occurred_at": "2026-09-20T10:32:11Z",
  "actor": { "id": 12, "name": "Jérémy Buget", "email": "j.buget@waat.fr" },
  "data": {
    "user": { "id": 12, "name": "Jérémy Buget" },
    "month": "2026-09",
    "total_days": 18.5,
    "by_project": [
      { "id": 41, "name": "WAATcher", "days": 12.0 },
      { "id": 58, "name": "Congés", "days": 6.5 }
    ]
  }
}
```

- **snake_case**, like the rest of the API. The catalogue's camelCase is
  waat.tools's vocabulary and stays confined to `CatalogEntryResponse`.
- `actor` is null when nobody caused the event. In V1 it never is; the field
  exists so the temporal events do not force a shape change.
- **No version number.** The contract is instead: *fields are added, never
  removed and never renamed*. A version number invites a v2 and doubles the
  mapping; an additive rule costs nothing and is easier to keep.
- **`data` carries what the event is about, and not the whole object.** A
  consumer that needs the rest has an API and a key.

### What never travels

Moods, obviously. But also: **no day-by-day entry ever appears in a payload.**
`month.validated` carries a total and a split by project, which is what an
invoicing or reporting reader needs, and stops there. Whoever needs the grid
reads `GET /api/v1/entries` with a key, under a scope, leaving a trace.

### Retries

| Attempt | After |
|---|---|
| 1 | immediately |
| 2 | 1 min |
| 3 | 5 min |
| 4 | 30 min |
| 5 | 2 h |
| 6 | 6 h |

A 2xx is a success. Anything else, or a timeout at 10 s, is a failure. `410
Gone` stops the retries at once and suspends the subscription — the consumer
has said the endpoint is dead, and insisting for nine hours is rude.

After the sixth attempt the delivery is **abandoned**, and abandoned deliveries
are kept: they are what the screen shows, and what « Rejouer » replays.

**Ten consecutive abandoned deliveries suspend the subscription**, with the
reason and the date. Without that rule a Slack channel deleted in January has
Ganesh knocking on it in June, every hour, forever.

---

## Security

The dangerous half of a webhook is not the secret. It is that **a manager can
make the production host issue an HTTP request to an address of their
choosing**, from inside the VPC, holding an instance role. Server-side request
forgery, handed over on a form.

So, before any delivery:

- **HTTPS only.** No `http://`, no other scheme.
- **The address is resolved, and the resolved IP is checked** — not the
  hostname. Refused: loopback, link-local (`169.254.0.0/16`, which is the EC2
  metadata endpoint), every RFC 1918 range, and anything that is not a global
  unicast address. Checking the hostname alone is defeated by a DNS record
  pointing at `127.0.0.1`, which anyone can create.
- **Redirects are not followed.** A 30x is a failure, with that as the reason.
- **10 s timeout**, connection included, and a cap on the response read: the
  body is discarded, only the status matters.
- The rule is checked **at delivery**, not only at creation. A hostname that
  resolved publicly in March can resolve to `10.0.0.5` in April.

The one remaining loop is a consumer that reacts to an event by calling the API
back with a key, which writes, which fires an event. The payload names the
actor precisely so the consumer can ignore its own service account, and the
documentation says to.

---

## Technical design

### A new module

```
server/src/modules/webhooks/
├── domain/
│   ├── entities/         WebhookSubscription, WebhookEvent, WebhookDelivery
│   ├── services/          signing.py, backoff.py, event_mapping.py, url_policy.py
│   └── repositories/      WebhookSubscriptionRepository, WebhookEventRepository,
│                          WebhookDeliveryRepository, WebhookSender (port)
├── application/           use cases: manage, list, replay, and DispatchDueDeliveries
├── infrastructure/        SQLAlchemy models + repos, HttpWebhookSender,
│                          PublishingAuditLogRepository (the decorator)
└── presentation/          routes, schemas, dependencies
```

`WebhookSender` is a domain port. The relay's use case therefore tests against
an in-memory sender that records calls — no HTTP, no mock of a mock — and the
one implementation that speaks `httpx` carries the URL policy and nothing else.

### Where events are born: a decorator, not a new dependency

Two ways to get an event out of a gesture.

**Inject a publisher into every use case**, beside the audit repository. Honest
and explicit — and it adds a constructor argument to some twenty use cases, and
reintroduces exactly the failure the audit log already has: a new use case that
forgets to call it. CLAUDE.md already names that failure (« a new one that does
not is a gap »). Doing it twice doubles the gap.

**Decorate the audit repository.** Every use case that writes already takes an
`AuditLogRepository` and already calls it. Wrapping the port means every traced
gesture is a candidate event, for free, forever:

```python
class PublishingAuditLogRepository(AuditLogRepository):
    """Writes the line, and the event the line stands for."""

    def __init__(self, inner: AuditLogRepository, events: WebhookEventRepository) -> None: ...

    async def add(self, log: AuditLog) -> AuditLog:
        written = await self._inner.add(log)
        await self._publish(written)
        return written
```

Wired in `dependencies.py`, one line, in `get_audit_log_repository`. The
decorator lives in `webhooks/infrastructure/` and imports `audit_logs.domain`:
webhooks depends on the audit log, the audit log knows nothing of webhooks, and
no import-linter contract is touched.

The property this buys is the one that matters in a year: **a gesture that
leaves a trace is a gesture that can be announced.** Adding a use case gets you
the event or an explicit refusal, never silence.

### The test that keeps the catalogue honest

```python
def test_every_audit_action_is_either_broadcast_or_explicitly_silent():
    for action in AuditAction:
        assert action in EVENT_MAPPING or action in DELIBERATELY_SILENT
```

`DELIBERATELY_SILENT` holds `ENTRY_SET`, `ENTRY_CLEAR`, `MONTH_PROJECT_ADD`,
`MONTH_PROJECT_REMOVE`, `SIMULATION_*`, `API_KEY_UPDATE`, `USER_IDENTITY_UPDATE`
— each beside the reason. Adding a 28th `AuditAction` breaks this test until
somebody decides. That is the whole point.

### One gesture, one event

`trace_project_changes` writes **one audit line per field**. A PATCH moving the
phase, the axis and the estimate writes three, on purpose — the project's
Journal tab is read field by field.

A naive mapping would send three webhooks for one click. So the decorator
**coalesces within the request**: it holds a buffer keyed by
`(event, subject)`, and a second line on the same key appends to the row
already written rather than inserting another.

```python
# first line   → INSERT webhook_event(..., data={"changes": [{"field": "status", …}]})
# second line  → the same row, data["changes"].append({"field": "category", …})
```

It works because the decorator is built **per request** (it is a FastAPI
dependency) and the route commits once: one HTTP request is one unit of work is
one gesture. Each row also carries a `gesture_id` — a `uuid4` minted when the
decorator is constructed — so the grouping is a recorded fact rather than an
inference, and two gestures on the same project a second apart never merge.

`project.status_changed`, `project.published` and `project.went_live` are read
out of the `changes` of a `project.update` line, by the mapping, and are emitted
**beside** `project.updated` rather than instead of it. A consumer that
subscribed to phases gets phases; one that wanted everything still gets
everything.

### The outbox, and why the event is written in the gesture's transaction

`SqlAuditLogRepository.add()` flushes; the **route** commits. Between the two,
the gesture can still fail — a constraint, a second repository refusing. An
event sent at `add()` announces a validation that never happened.

So the decorator does not send. It **writes a row** — `webhook_event`, status
pending — in the same session. The route's `await session.commit()` makes the
fact and its announcement atomic, at zero cost, because that commit already
exists on every write route in the product.

This is the transactional outbox, and it is the reason `BackgroundTasks` is
refused: a FastAPI background task holds the queue in the process and loses it
at the next deploy, which happens on every push to `main`.

### Fanning out: one fact, N deliveries

`webhook_event` is the fact, written once, whatever the subscriptions are. The
relay turns it into one `webhook_delivery` per matching subscription.

The write path therefore never reads the subscription table — no extra query on
the hot path, and no race between « somebody is validating a month » and
« somebody is editing a subscription ». It also leaves, for free, a readable
stream of what happened, which is what the screen shows and what a future SSE
feed would read. That is a consequence, not a goal: nothing else reads it in V1.

### The relay

One `asyncio` task, started in the app's lifespan, waking every few seconds:

```sql
SELECT * FROM webhook_delivery
 WHERE status = 'pending' AND next_attempt_at <= now()
 ORDER BY next_attempt_at
 LIMIT 20
 FOR UPDATE SKIP LOCKED;
```

`FOR UPDATE SKIP LOCKED` is what makes this safe the day the host runs more
than one uvicorn worker — each takes what the others are not holding, and
nobody delivers twice. It costs one clause and removes an assumption the API
already makes elsewhere (`InMemoryRateLimitStore` counts per process, and says
so). No reason to make the same bet twice.

No Celery, no Redis, no second container. The deployment is one image on one
ARM host behind Caddy; adding a broker to send a few hundred HTTP calls a day
would be infrastructure bought against a problem nobody has.

The same task purges: deliveries and events older than 30 days.

### The secret: derived, never stored

A webhook secret cannot be hashed the way an API key is — we have to re-sign
with it on every delivery. Storing it in plain text sits badly beside a project
that keeps no secret in the database and none in Terraform's state.

So it is derived rather than stored:

```python
secret = "ghsec_" + urlsafe_b64(hmac_sha256(SECRET_KEY, f"webhook:{id}:{version}"))
```

Nothing to encrypt, nothing to leak from a dump, and rotation is
`version += 1` — one small integer column. `SECRET_KEY` already signs the
sessions and is already per-environment and out of band, so a webhook secret
cannot be forged from another environment's.

The trade-off, stated plainly: rotating `SECRET_KEY` invalidates every webhook
secret. It already invalidates every session, so the day it happens is already
a day with a procedure.

The simpler fallback, if derivation feels like too much cleverness: a plain
column, shown once, never handed back. Same interface, weaker at rest.

### The tables

```
webhook_subscription
  id, name, url, events (JSON list of strings),
  secret_version (int, default 1),
  owner_id → users.id, created_by → users.id, created_at,
  suspended_at, suspended_reason, revoked_at, revoked_by,
  consecutive_failures (int), last_success_at, last_failure_at

webhook_event
  id, uuid (unique), gesture_id, event (enum), occurred_at,
  actor_id → users.id (nullable), project_id → projects.id (nullable),
  target_user_id → users.id (nullable),
  data (JSON), fanned_out_at (nullable)
  index (fanned_out_at), index (occurred_at)

webhook_delivery
  id, uuid (unique), subscription_id → …, event_id → …,
  status (enum: pending | delivered | abandoned),
  attempts (int), next_attempt_at, 
  last_status_code, last_error, last_attempt_at, delivered_at
  index (status, next_attempt_at)
```

`event` and `status` are `Enum(..., native_enum=False)`, like every other
enumeration in the schema: the **name** of the Python member is what lands in
the column. Three models, imported in `alembic/env.py`, one migration.

Foreign keys to `users` and `projects` are `ON DELETE SET NULL`, as `audit_log`
does: a delivery survives what it was about, and the payload it already carries
says what that was.

### Routes

| Route | Who |
|---|---|
| `GET /api/v1/webhooks` | Everyone |
| `POST /api/v1/webhooks` | Manager. Returns the secret, once |
| `PATCH /api/v1/webhooks/{id}` | Manager. Name and events; never the URL |
| `POST /api/v1/webhooks/{id}/rotate-secret` | Manager. Returns the new secret, once |
| `POST /api/v1/webhooks/{id}/resume` | Manager. Lifts a suspension |
| `DELETE /api/v1/webhooks/{id}` | Manager. Revokes |
| `GET /api/v1/webhooks/{id}/deliveries` | Everyone, paged |
| `POST /api/v1/webhooks/deliveries/{id}/replay` | Manager |
| `GET /api/v1/webhooks/events` | Everyone. The catalogue, so the form is not a hardcoded list on the client |

All depend on `get_current_user` / `get_current_manager`. **No API key scope in
V1**: a machine that could mint a subscription could point Ganesh at itself.
Administering the door is a human gesture.

Changing the URL is not offered: the secret is bound to the subscription, and
silently repointing an endpoint that a channel trusts is the kind of edit
nobody notices. Revoke and create.

Every one of those gestures writes to `audit_log`, under three new actions —
`WEBHOOK_CREATE`, `WEBHOOK_UPDATE`, `WEBHOOK_REVOKE` — which the mapping lists
as deliberately silent.

---

## The screen

A tab beside « Clés API » in the settings, because it is the same reader doing
the same kind of thing.

- **`WebhooksTable`** (organism) in the shared frame: `TABLE_FRAME`,
  `TABLE_HEADER`, `STRONG_SEPARATOR` closing the name column, square corners,
  white naming cell. The state is a coloured dot then a plain label — « Active »,
  « Suspendu », « Révoqué » — never a filled badge.
- A row reads: name, URL, how many events, owner, state, last success.
- **A detail panel** lists the last deliveries: event, when, HTTP status,
  attempts, and « Rejouer ». This is the screen that gets opened when Slack
  goes quiet, and it must answer in one look whether Ganesh sent it.
- The creation form lists the events grouped by subject, each with its French
  one-liner, read from `GET /webhooks/events`.
- The secret is shown once, in a panel that says so, with a copy button — the
  same wording as API keys.

French labels, `cursor-pointer` on everything clickable, the event names left
in English inside `<code>`: they are what the consumer's code will match on.

---

## Out of scope for V1

- **Temporal events.** No scheduler. See above.
- **Filtering beyond the event** — by axis, by department, by project. Every
  consumer we have wants everything on its events. Add it when one does not.
- **A per-project subscription.** Same reasoning, and it multiplies the table.
- **Slack as a first-class target.** A Slack incoming webhook wants its own
  payload shape; V1 sends Ganesh's shape and an n8n or a small relay translates.
  Building a formatter per destination is a product of its own.
- **Replay of a whole window** (« resend everything since Tuesday »). Replay is
  per delivery. The events are kept 30 days, so the door stays open.
- **Webhook management by API key.** See above.
- **`*` as an event list.** A subscription says what it wants, so adding an
  event never silently starts sending it somewhere.

---

## Delivering it

Three slices, each shippable and each useful on its own.

**1 — The spine.** The module, the three tables, the decorator, the outbox, the
relay, the signature, the URL policy. Four events only: `month.validated`,
`month.reopened`, `project.status_changed`, `update.posted`. A read-only screen
listing subscriptions and deliveries; subscriptions created by migration or by
hand. This is where the design is proven, on the smallest surface that can
prove it.

**2 — The catalogue and the screen.** The rest of the events, the three derived
ones included (`project.published`, `project.went_live`, `project.archived`),
the exhaustiveness test, the full management screen: create, rotate, suspend,
resume, revoke, replay.

**3 — Whatever turns out to be missing.** `docs/webhooks.md` becomes the
reference rather than the brief, as `docs/api-keys.md` did, and the first line
of this file changes.
