# Teams notifications (brief)

> **Set aside on 2026-09-23.** Nothing of this exists in the code, and nothing
> is planned. The bell stays the only place a notification is read.
>
> It is kept because the question will come back — people do not see the bell
> — and because the ground was covered: browser push weighed and dropped, the
> four things called « a Teams app » compared, and the two consents gating the
> good one identified as hard administrator gates with no way round them.
> Whoever picks this up starts at *Decisions taken*, not from nothing.
>
> What would bring it back: wanting a notification to reach somebody who is
> not looking, badly enough to open a ticket with IT. Had it gone ahead, the
> decision was the registered app and not the workflow — the reasoning is in
> *The contingency, if the consent stalls*.

## The gap it closes

The bell works. What it cannot do is reach somebody who does not have Ganesh
open, which is most of the team most of the day. A mention waits until the
next visit, and a month reopened on Friday is discovered on Monday.

Browser push was the first answer considered and dropped: it asks each person
for a permission they refuse by reflex, it needs a service worker and a
bundling step the client does not have, and on iOS it only works for whoever
installed Ganesh on their home screen. The team is in Teams all day, signed in
with the same Entra identity Ganesh already provisions from. That is the tuyau.

**Teams is a canal, not a second inbox.** The line it shows points at Ganesh;
`read_at` stays where it is. Nothing of the notification module's design
changes — a second way out is added beside the bell, on the seam every
producer already goes through.

## What is being asked of IT

Three things, on the `Ganesh - Production` tenant. Nothing else in this brief
is blocked on anybody.

| What | Why |
|---|---|
| A new app registration, **`Ganesh - Teams notifier`** | A daemon identity, separate from the sign-in app. See *The identity the API gains* |
| Admin consent on **`TeamsActivity.Send`** (application) | Lets Ganesh put a line in somebody's Teams activity feed |
| Admin consent on **`TeamsAppInstallation.ReadWriteSelfForUser.All`** (application) | Lets Ganesh install *its own* app for a teammate, so nobody has to go and add it. It grants nothing over any other app |
| Upload of the Ganesh app manifest to the **org app catalog** | The activity feed will not accept a notification from an app it does not know |

What is **not** asked, and worth saying out loud because it is what makes the
ask small: no permission to read anybody's messages, no permission to read a
chat or a channel, no bot, no public endpoint, no access to any mailbox.
Ganesh writes one kind of object — a notification addressed to one person —
and reads nothing.

### Which of those a non-admin can do alone

None of the consents. This is worth being exact about, because it decides
whether this brief is reachable at all:

| Step | Needs an admin? |
|---|---|
| Create the app registration | **Sometimes.** Entra's *Users can register applications* is on by default; many orgs turn it off. Two minutes to find out |
| Consent to `TeamsActivity.Send` | **Always.** It is an *application* permission, and application permissions can only ever be consented by an admin. There is no workaround, no delegated variant that avoids it for a daemon |
| Consent to `TeamsAppInstallation.ReadWriteSelfForUser.All` | **Always**, same reason |
| Put the app in the org catalog | **Yes** for the team. Sideloading a custom app gets *you* a test install if the tenant allows it, but the notification has to land on the **recipient's** install, so sideloading never reaches the team |

**So: no admin, no activity feed.** Two consents are hard gates with nothing
behind them to negotiate — which is why the ticket goes out first and the rest
of the work happens while it is in flight.

## What we owe the ticket

A consent is easier to grant when there is nothing left to guess. Four things
to hand over:

- **The app manifest and its icons** — a `manifest.json` declaring the three
  activity types and their French templates, a colour icon at 192×192 and an
  outline icon at 32×32. This is ours to write, it needs nobody, and it is the
  thing being deposited. Write it before opening the ticket.
- **The registration, owned by the organisation.** Ask for **at least two
  owners** in Entra. An app registered under one person's name reproduces
  exactly the fragility that argues against the flow, only with better
  paperwork.
- **The permissions, each with one line of justification**, and — as
  importantly — the list of what is *not* asked.
- **A named contact on our side**, and where the runbook lives
  (`docs/deployment.md`).

### Two things that outlive the ticket

- **The client secret expires**, in six, twelve or twenty-four months
  depending on tenant policy. When it does, notifications stop and nothing
  else breaks — which means they stop **silently**, and nobody finds out for a
  week. Record the expiry date beside the Parameter Store entries in
  `docs/deployment.md`, and ask the administrators whether a certificate or a
  federated credential is available instead: a credential that cannot quietly
  lapse is worth asking for while somebody is already reading the request.
- **An authentication failure is loud; a send failure is not.** One
  notification lost to a timeout is by design (see *Sending, and failing*). A
  token refused is not a lost notification — it is the feature being off — and
  it must be logged as an error rather than swallowed with the rest.

## Decisions taken

| Question | Decision |
|---|---|
| Which Teams surface | **The activity feed**, addressed to one person |
| Addressed to | **One person**, by `entra_oid`, which `User` already carries |
| Who receives | Exactly the fan-out the bell already computes. Never more |
| What rings | Three kinds, and the criterion is *somebody is waiting on you* |
| Where a line leads | **The inbox**, `/notifications` — one address, composed nowhere else |
| Direction | **Ganesh → Teams only.** Same rule as Monday |
| Identity | **A second app registration**, holding a client secret the API did not have |
| New tables | **None** |
| When it is sent | After commit, in the background. A lost push is lost |
| How it is sent | One port. **Graph, from an app registered on the tenant.** The flow adapter is a contingency, written only if the consent stalls |
| Who owns the app | **The organisation**, with at least two owners in Entra. Never one person |
| Muting | In Teams, per app. Not a screen in Ganesh |

## Why the activity feed, and not the three others

Four things get called « a Teams app », and they cost wildly different
amounts.

- **A Power Automate workflow** posting to a channel. Nearly free, no consent,
  no catalog. But a channel is a **broadcast**: it tells eleven people what
  concerns one, and it cannot say « vous avez été mentionné » because it is
  addressed to nobody. Kept as the fallback, and as the right shape for La
  Gazette, which is a broadcast already.
- **The activity feed.** Addressed to a person, lands on desktop and mobile,
  no permission for anyone to refuse, deep link back. This one.
- **A bot.** 1:1 messages and buttons that write back. Costs an Azure Bot
  resource, a public endpoint to maintain, and stored conversation references.
  It is also the only door to a 1:1 chat message from a daemon — sending one
  needs `ChatMessage.Send` as an application permission, which is behind
  Microsoft's protected-API request process. The activity feed is the right
  door precisely because it is not.
- **A Teams tab embedding Ganesh.** A decision about where Ganesh lives, not
  about notifications. Out of scope, and it should stay a separate question.

## Where it plugs in

`NotificationDelivery.deliver()` — `src/modules/notifications/domain/services/delivery.py`.

It is the one place every producer already goes through, and the fan-out has
already done the two things that matter: taken the actor out, and folded a
repeat into the line that was waiting. A Teams adapter grafted anywhere else
would have to redo both, and would get one of them wrong.

The port goes in the domain beside `NotificationRepository`:

```
src/modules/notifications/domain/ports/activity_feed.py   # ActivityFeed (ABC)
src/modules/notifications/infrastructure/teams/graph_activity_feed.py
```

Same shape as `AttachmentStore` / `S3AttachmentStore` and
`ProseWriter` / `GeminiProseWriter`. The domain knows there is somewhere to
announce a line; it does not know it is Microsoft.

One call carries a whole `deliver()`:
`POST /teamwork/sendActivityNotificationToRecipients` takes up to a hundred
recipients for one notification. A `deliver()` is handed a homogeneous list —
same kind, same actor, same project — so it maps to exactly one call. The
mentions and the rest are two `deliver()` calls today, and become two Graph
calls, which is right: they say different things.

## What rings, and what does not

A new property beside `accumulates`, on `NotificationKind`, in the domain and
under test:

```python
@property
def interrupts(self) -> bool:
    """Whether this is worth reaching somebody who is not looking."""
```

V1 says yes to three:

| Kind | Why |
|---|---|
| `UPDATE_MENTION` | Somebody spoke to you and is waiting for an answer |
| `PROJECT_ASSIGNED` | You are expected on a mission you did not know about |
| `MONTH_REOPENED` | Your month was handed back to you to finish |

And no to everything else. The criterion is **somebody is waiting on you**,
not *this matters*. A role change matters and asks nothing of you; twenty-two
cells filled in your month matter and ask nothing of you. `TIMESHEET_EDITED`
accumulates and `PROJECT_UPDATE_POSTED` fires all day — either of them ringing
on a phone is how a team learns to mute the app, and a muted app rings for
nothing ever again.

The next kind earns its place by being asked for.

## What a line says

Here is the one real friction, and it is worth understanding before writing
any code.

The French of the inbox lives in `client/src/lib/notifications.ts`, in the
`WORDINGS` table, under test. Teams will not read it: the activity feed
composes its text from a **`templateText` declared in the app manifest**, with
named parameters filled at call time. So one activity type is declared per
interrupting kind, and its French lives in the manifest:

```jsonc
// manifest: activities.activityTypes
{ "type": "mention",       "description": "Mention dans une mise à jour",
  "templateText": "{actor} vous a mentionné sur {project}" },
{ "type": "assignment",    "description": "Affectation à un projet",
  "templateText": "{actor} vous a ajouté à {project}" },
{ "type": "monthReopened", "description": "Mois rouvert",
  "templateText": "{actor} a rouvert votre mois de {month}" }
```

That is a second place French is written, and the project's rule is that a
thing is written once. The resolution is not to pretend otherwise but to make
the drift impossible:

> **A kind that interrupts and has no activity type in the manifest is a bug,
> and a test says so.** The same trick as a scope that opens no route: the
> test reads the manifest, reads the kinds where `interrupts` is true, and
> fails on either side of the difference.

The duplication is then bounded — three short strings — enforced, and honest.
It also stays small by design: Teams says only what it takes to decide whether
to click, and the sentence the inbox writes stays richer. **The Teams line
points; it does not copy.**

## Where a line leads

`/notifications`, on the absolute address of the client. Not the project
panel, not the update.

The deep link to a single update exists — `panelAddress()` in
`client/src/lib/opened-mission.ts`, which is what the inbox line already uses.
Composing it server-side would mean building that address in a second place,
in another language, and keeping the two in step forever. Landing in the inbox
costs one extra click and buys: one address, composed once, that never changes
when a kind is added; and the person lands where the read state lives, which
is the thing Teams cannot do for them.

The day the extra click is judged too expensive, the way out is to move the
address composition somewhere both sides read — not to copy it.

This needs one thing the API does not have: **it does not know the client's
URL.** `api_url` is in `src/core/config.py`; there is no `web_url`. Add it,
default `http://localhost:3000`, set to `https://ganesh.waat.tools` in
production.

## The identity the API gains

Today the API holds no Entra secret at all. `CLAUDE.md` records why: the BFF
carries the OAuth flow and holds `AZURE_AD_CLIENT_SECRET`; the server only
validates tokens and needs nothing but a tenant and a client id.

Calling Graph as a daemon changes that. The API will hold a client secret and
acquire tokens by client credentials. That is a real change to what the API
is, and it is the reason for a **separate app registration** rather than
adding application permissions to the sign-in app:

- The secret lives on the API alone, and rotating or revoking it logs nobody
  out.
- The sign-in app keeps exactly the permissions it has, which is none of
  these.
- The consent ask is one app that does one thing, which is a great deal easier
  to get approved than a broad permission on the app everyone signs in with.

New settings, beside `gemini_api_key` and the S3 block:

```python
teams_tenant_id: str = ""      # the same tenant, named for this use
teams_client_id: str = ""
teams_client_secret: str = ""  # Parameter Store in production, never Terraform
teams_app_id: str = ""         # the catalog id of the Ganesh Teams app
web_url: str = "http://localhost:3000"
```

All optional, all empty by default. **Without them nothing breaks** — the same
contract `GEMINI_API_KEY` already has. The adapter is a no-op, the bell keeps
working, and no developer needs a tenant to run the project.

## No new table

The activity feed needs no subscription: `User.entra_oid` is already the
address, and muting lives in Teams, per app, where the person expects to find
it. Nothing to store, nothing to expire, no screen to build. This is the
cheapest part of the feature and it is worth not spending it.

One wrinkle: the notification only lands if the Ganesh app is installed in the
person's personal scope. Rather than a column tracking that, install lazily —
send, and on the error that says the app is not installed, install it with
`TeamsAppInstallation.ReadWriteSelfForUser.All` and send again. It costs one
extra round trip once per person, ever.

## Sending, and failing

`deliver()` is awaited inside the use case's transaction. An HTTP call to
Graph must not be: it would put a network round trip, and somebody else's
outage, in the middle of every gesture that notifies.

So: **after commit, in the background.** And the guarantee is stated rather
than engineered around —

> A Teams notification lost on a restart, a timeout or a Graph outage is
> lost. The line is in the inbox regardless, and the bell is the truth.

That is what makes it acceptable to have no queue, no outbox table and no
retry beyond the one the HTTP client does on its own. The day it is not
acceptable, an outbox row written in the same transaction is the upgrade, and
it fits without moving the seam.

## Traceability, and what is never said

- **A Teams notification is not traced in `audit_log`.** It is a channel, not
  a gesture — the same reason a sign-in and a reaction are outside it.
- **Nobody is named in a bad light, in a channel or anywhere else.** The rule
  already exists twice, in `Highlight` and in the MCP server's refusal to
  carry a mention. It is written here because a channel is exactly where
  somebody will want to post « il manque le mois de X, Y et Z », and that must
  be a decision, not a slip.
- **A notification body is read on a lock screen.** The mention template names
  the actor and the project and stops there. No excerpt of what was written.
- **Ganesh → Teams, one way.** Nothing Teams sends comes back in. A bot that
  replied would be a new door into the domain, and every invariant would have
  to be re-argued at it.

## Out of scope

- Browser push. Decided against; doing both means three places the same thing
  rings and two read states to reconcile.
- A bot, buttons, replying from Teams, marking read from Teams.
- A Teams tab embedding Ganesh.
- Posting notifications to a channel. A channel is a broadcast and personal
  lines do not go in one — La Gazette later does, and belongs there.
- Any per-person preference screen in Ganesh.

## The contingency, if the consent stalls

Not the plan, and to be written only if the ticket is still open when that
starts to cost something. A **Power Automate workflow**, created from a Teams channel's own menu by an
ordinary member, triggered by an HTTP request, that sends the message as the
Flow bot. Two shapes, and the second is the interesting one:

- **To a channel.** A broadcast. Right for La Gazette, wrong for the bell.
- **To a person** — *Post message in a chat or channel*, posting as **Flow
  bot**, into the chat with Flow bot, recipient given per call. This is a 1:1
  DM, addressed to one teammate, with **no admin anywhere in the picture**.

Ganesh sends the same thing either way: one HTTP POST carrying the recipient,
a sentence and a link. The flow fans nothing out and decides nothing — it is a
relay.

### What it costs

- **The message comes from Flow bot**, not from a Ganesh-branded app. It works
  and it looks like what it is: a robot relaying something.
- **It belongs to whoever created it.** One person's account, one person's
  seeded Power Automate licence. They leave, it stops. That is a real
  dependency on a human, and it should be written down somewhere other than
  their memory.
- **The trigger URL is the credential.** Anyone holding it can make the flow
  DM anyone in the tenant. Put a shared secret in the payload and have the
  flow drop anything that does not carry it.
- **It can be switched off above you.** Power Automate, or the Teams
  connector, can be restricted tenant-wide. Less commonly than app
  registration, but it is the same class of risk — it is just not being
  exercised today.

### Why this does not compromise the design

**The port is the same.** `ActivityFeed` describes *announcing a line to a
person*; whether the adapter talks to Graph or POSTs to a flow URL is an
infrastructure detail, and the domain never learns which. So:

```
domain/ports/activity_feed.py          ActivityFeed (ABC)
infrastructure/teams/flow_activity_feed.py    ← ships now, no admin
infrastructure/teams/graph_activity_feed.py   ← the day consent lands
```

Everything else in this brief — `interrupts`, the seam in `deliver()`, sending
after commit, `web_url`, landing in the inbox, nothing traced in `audit_log` —
is unchanged and is written once. So the contingency costs one file, and
falling back to it undoes no work.

It stays a contingency for the reasons that decided this brief: a flow belongs
to a person's account and their licence, its trigger URL is a bearer
credential nobody can audit centrally, its failure the day that person leaves
is silent, and in two years « Flow bot » tells no reader what is messaging
them or why.

## Three things to check yourself, before writing the ticket

All self-service, no permission needed to look, about ten minutes total. They
tell you how much the ticket has to ask for — and whether the contingency is
even available if it stalls.

1. **Teams → a channel → ⋯ → Workflows.** If you can create one from
   *When a Teams webhook request is received*, the no-admin path is open. Go
   one step further and confirm that *Post message in a chat or channel* lets
   you post **as Flow bot** into a chat with a named person — that is the
   whole feature, and it is the one thing worth verifying by hand rather than
   trusting a note.
2. **portal.azure.com → App registrations → New registration.** If it refuses,
   even the first step of the Graph path needs a ticket.
3. **Teams → Apps → Manage your apps → Upload a custom app.** If it is absent,
   custom apps are off tenant-wide, and the Graph path needs that turned on
   too — a third thing on the ticket, and the one most likely to be refused on
   policy grounds.

## How to ask

One request carrying all three consents, the manifest attached, and the list
of what is *not* being asked stated as plainly as what is. An app-only
permission that posts a notification and can do nothing else is easy to
approve once it is described precisely, and frightening when it arrives as
« accès à Teams ».

Give a date rather than an urgency. The work on Ganesh's side does not wait on
the answer — only the last adapter does — so the honest framing is « nous
livrons sans, et nous branchons dessus quand vous ouvrez ». It is also the
framing most likely to be read the day it lands.

## What to verify before building

The Teams and Graph surface moves — the retirement of the old Office 365
connectors is the current illustration. Confirm against Microsoft's docs at
the time of building, not against this note: the exact permission names, the
manifest schema version and the shape of `activities.activityTypes`, the
`topic` form for an external `webUrl`, and the throttling limits on
`sendActivityNotificationToRecipients`.

## Files that would change

| File | What |
|---|---|
| `server/src/modules/notifications/domain/entities/notification.py` | `interrupts`, beside `accumulates` |
| `server/src/modules/notifications/domain/ports/activity_feed.py` | New port |
| `server/src/modules/notifications/domain/services/delivery.py` | Announce, after writing |
| `server/src/modules/notifications/infrastructure/teams/` | Graph adapter, token cache, lazy install |
| `server/src/core/config.py` | `teams_*`, `web_url` |
| `server/tests/modules/notifications/` | `interrupts`, the manifest/kinds test, a fake feed |
| `teams/manifest.json` + icons | The app deposited in the catalog |
| `docs/deployment.md` | The four parameters to put in Parameter Store |
