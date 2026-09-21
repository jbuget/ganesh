# MCP server (V1)

> **Built.** This was the design brief; it is now the reference for what
> shipped. The server lives in `server/src/mcp/`, and *Deliberately out of V1*
> still says what was left out on purpose.

## The gap it closes

The team already has Claude Code open all day. Ganesh knows things nobody goes
looking for, because looking means leaving the terminal for a tab: what a
month is missing, what moved on a project one is not on, which mission is
called what.

The API already lets a machine in — `jns_` keys, eleven scopes, a rate limit,
an owner who answers for each key. What it does not have is a way for a model
to *ask*. An MCP server is that: the same reads, reachable from the sentence.

This is the third attempt at putting a model near Ganesh. The first two — a
« Revue » screen, a summary of a project's thread — were dropped at framing,
both on the same finding: *the reader already knows*. The difference here is
that neither the interface nor the questions are ours to invent. The client
brings them. What stays ours is **what Ganesh knows how to say**, which is a
much smaller problem.

## Decisions taken

| Question | Decision |
|---|---|
| Transport | Streamable HTTP, mounted at `/mcp` inside the API |
| SDK | `mcp` 2.2.0 — where `FastMCP` is called `MCPServer` |
| Who a key belongs to | **A person**, for these keys. The first assumed exception to *service accounts only* |
| What a tool calls | **A use case**, never the API's own HTTP routes |
| What a tool returns | Sentences carrying facts, not a JSON row |
| Client | Claude Code and Claude Desktop, by static header |
| V1 verbs | Five reads, and one write — on the caller's own month |
| V1.1 verbs | Two reads more — a project's sheet, and the whole register read across |

## Where it lives

`src/mcp/`, a top-level package beside `src/modules/`, `src/common/` and
`src/shared/`.

Not a module: it crosses every module, and a `presentation/` that reached into
five others would be the first one to do so. Not `common/` either, which is
forbidden to know a business module at all. It is a **second presentation**,
parallel to the routers — the same use cases, a different way in.

Two `import-linter` contracts hold it in place:

- `src.mcp` may import `src.modules.*.application` and
  `src.modules.*.presentation`, and nothing of any domain or infrastructure it
  does not already reach through those.
- **Nothing imports `src.mcp`** but `src.main`. A module that came looking for
  a tool would have inverted the direction the whole architecture runs in.

## The socle

### The transport

`app.mount("/mcp", …)` in `src/main.py`, beside the routers.

Three things cost an afternoon each to whoever meets them blind:

- **The lifespan does not cross a `mount`.** Starlette runs the root
  application's alone, so `ToolServer.lifespan` is handed to `FastAPI(...)` and
  the API adopts it. Without it the first call dies on « task group is not
  initialized ».
- **The session manager runs once per instance**, and refuses a second start.
  That is why `ToolServer` is a class rather than a module of globals: a test
  that stands up its own API gets its own server.
- **The address carries a trailing slash.** The app is mounted at `/mcp` and
  its own route is `/`, so `/mcp/` is what answers and `/mcp` redirects to it
  with a `307` — which keeps the method and the body, so a client that follows
  redirects never notices.

Lifting the SDK in lifted the framework with it: `mcp` pulls starlette 1.x,
which FastAPI refused until 0.141. The suites, mypy and the import contracts
came through untouched; the only visible change is two optional fields on the
generated client's `ValidationError`.

### The door

`Depends` does not cross a mount: FastAPI resolves dependencies for its own
routes, and everything under `/mcp` is somebody else's ASGI app. So the door is
an **ASGI middleware** wrapped around the mounted app, doing by hand what
`require_scope` does by declaration:

1. read the bearer off the header, and the `jns_` prefix that tells one of ours;
2. `AuthenticateApiKeyUseCase` — the same use case, the same seam a test stands
   in for;
3. `CheckRateLimitUseCase`, against the same in-memory store;
4. put the resulting `Caller` in a **contextvar**, which is what a tool reads
   to know who is asking.

A call without a key, or with one that is expired, revoked, or owned by a
deactivated teammate, never reaches a tool — not even to be told what the
tools are: a list of tools is a map of the product. There is no human door on
`/mcp`, because nobody signs in with Entra from a terminal client.

The door **identifies** rather than authorises: which scope a call needs
depends on the tool asked for, and the door reads the envelope. That is what
`AuthenticateApiKeyUseCase.identify` was added for — the same five refusals as
`execute`, without a scope to check yet.

### Scopes stay honest

`@answers(scope)` is one line above a tool and carries two things:

- **the scope is registered in `OPENED_SCOPES`**, exactly as a route registers
  its own. `test_every_scope_the_form_offers_opens_a_route` reads that same
  set; a tool is now one of the things a scope may open. The property the test
  exists for — *the table of keys says what a key opens, and says it right* —
  is what must survive, not the word « route ».
- **a refusal comes out as a sentence.** The SDK hands a client the text of a
  `ToolError` and nothing else, so a business refusal is translated into one
  rather than swallowed as « Error executing tool ». A model told only that
  retries blind, or reports success.

### The session

One `AsyncSession` per tool call, opened and closed around it. V1 is read-only,
so nothing commits — except `last_used_at`, which the door writes through its
own freshness window, at most once a quarter of an hour per key.

### A refusal is a sentence

A tool that cannot answer says why, in words: « Aucun projet ne porte
l'identifiant 404 », « Le mois est validé : plus rien ne s'y écrit ». Every
`DomainError` raised underneath becomes one, through `@answers`. This is the
same reason `entry_router` gives for leaving writes human — and the reason
writing is out of V1 rather than out forever — and `declare_time` is what it
became once a tool could say those refusals in words.

## The tools

Eight, each `src/mcp/tools/<name>.py`, each answering in sentences built through
`src/mcp/tools/say.py` — « 1,5 jour », « 08/09 », « septembre 2026 ». A number
handed over raw is a number a model words itself, and words wrong.

### `find_project(query: str)`

**Scope** `projects:read`. The resolver the others lean on, and the reason a
model stops inventing identifiers.

Takes what a person would say — « waatcher », « le catalogue » — and returns the
few missions that match, each with its identifier, its kind, its phase and
whether it is still one to book against. Several matches are returned as
several; the choice is the caller's, and a tool that picked one would be
guessing.

> Trois projets portent ce nom. WAATcher (projet, en construction), WAATcher —
> Supervision (lot de WAATcher, en service), WAATcher V1 (archivé le 12 mars).

### `project_brief(project_id: int)`

**Scope** `projects:read`. `GetProjectDetailUseCase` — the mission's sheet, as
the screen reads it.

It closes the gap `find_project` left open: a model that had resolved a name
knew the identifier, the kind and the phase, and could say nothing about what
the mission had cost against what was planned. Two calls to answer « où en est
WAATcher », and the answer still short.

Three decisions carried in it:

- **the estimate is read as what is left.** « il en reste 22 » is the question
  being put; « 128 et 150 » is a subtraction a model gets wrong often enough to
  matter.
- **who carried it is named, never ranked.** `contributions` comes ordered by
  days, which is right on a screen showing the whole column at once. Handed to
  a model, that order becomes a sentence about who did the least. The people
  assigned are named; the ones who declared time are counted.
- **only `go_live_date` answers for a date.** A bar on the roadmap opens where
  the drawing needed it to, and reading that back would make a portfolio that
  announced nothing announce something.

> WAATcher (#7) — projet, construction depuis le 08/03/2026. 128 jours déclarés
> pour 150 estimés : il en reste 22. Mise en service annoncée le 30/11/2026.
> Porté par A. Ba. 2 personnes y ont déclaré du temps. 1 lot rattaché :
> WAATcher — Supervision (#8).

### `my_month(month?: str)`

**Scope** `entries:read`. `GetMonthGridUseCase`, for the **owner of the key and
nobody else**. The month reads `AAAA-MM`; without one, the current month.

There is no `user_id` parameter, and that is the guarantee: the target is
`caller.actor_id`, so there is no wrong colleague to hit. The route
`GET /entries/grid` stays human and untouched — one more reason the tools call
use cases rather than the API's own HTTP.

What it says: how much is declared against how many working days, what is
delivered and what is forecast, which days are still empty, and whether the
month is validated.

> 12 jours déclarés sur 19 ouvrés en septembre : 9 réalisés, 3 prévisionnels.
> Rien sur les 3, 4 et 5. Le mois est ouvert.

### `what_changed(project_id?: int, since?: str)`

**Scope** `audit:read`. Over a window that opens a fortnight back when nobody
says otherwise — the span somebody coming back from leave is asking about.

**Named a project, it reads that project's log** through
`ListProjectAuditLogUseCase`. **Named none, it reads the register** through
`ListAuditLogUseCase`, whose own docstring already says what it is for: *the
question an archive puts, and one no screen puts*. That second reading is what
the first was missing — a mission's « Journal » answers « what happened to this
project », and one has to already know which project to open.

The window is then told **project by project**, never as one chronology: a flat
list reads as the log it came from, the same mission picked up and dropped ten
times over. Missions come most-moved first and the tail is counted; gestures
carrying no mission are counted too rather than dropped, and a window wider
than one page says so.

> Depuis le 01/09/2026, 2 projets ont bougé :
> - WAATcher (#7) : passé de cadrage à construction le 08/09, 23 jours déclarés
>   par 4 personnes, et 6 autres gestes
> - NOMAD (#11) : une mise à jour postée, la dernière le 16/09
>
> 1 geste ne porte sur aucun projet.

This is the one angle that survived two framings: **nobody knows the projects
they are not on.** Asked after a fortnight away, or on a Monday about a
portfolio one does not follow.

It reads the project's log — which holds everything carrying its `project_id`,
declared time included — and returns a **delta**, not a digest: what changed
phase, what was posted on the thread, how much time went in and by how many
people. A month of raw log lines would be the summary that was dropped the
first time round.

It names three gestures and **counts** the rest (« et 12 autres gestes, que le
Journal du projet détaille »). That is what keeps the French wording here from
becoming a second copy of `client/src/lib/audit-log.ts`: two interfaces each
say the domain's vocabulary in French, and this one only ever learns the four
words it uses.

> Depuis le 1er septembre : passé de cadrage à construction le 8. Quatre
> personnes y ont déclaré 23 jours. Deux mises à jour postées, la dernière le
> 16. L'estimation n'a pas bougé.

### `portfolio_status(months?: int)`

**Scope** `roadmap:read`. The roadmap — the screen that is *shown* to a
committee rather than arbitrated. Planification answers a different question,
and it is arbitrated: a machine has no arbitration to make.

It does **not** read the bars out line by line: forty of them recited is the
screen without the drawing. The tally first, then the lines that put the
drawing in doubt — what is late, against the date announced, and what the
projection could not place at all.

> 64 projets sur la fenêtre, 0 en retard, aucune mise en service. À lire en
> sachant que 53 n'ont pas de date annoncée et 27 n'ont pas d'estimation.

### `team_mood()`

**Scope** `moods:read`, which no breadth covers. The fortnight in figures
nobody can be read out of: no name, no initials, no identifier, and a day
fewer than three people answered is announced rather than averaged.

The detail is in `docs/api-keys.md`; the thing to hold on to is that the
screen names everyone and never aggregates one person over time, and that a
model handed the names would do exactly that.

**Before this reaches the team, the team is told.** The moods were given to an
internal screen, and a frame changed quietly is what costs the answering rate.

### `declare_time(project_id: int, day: str, value: float)`

**Scope** `entries:write`, which no route opens. The corvée of the product,
done from the terminal already open.

**It writes on the month of the key's owner and no other.** There is no
`user_id` parameter, and that is the guarantee rather than an omission.
`PUT /entries` stays as it is, where a teammate may fix a colleague's month: a
person doing that has a screen in front of them.

Every refusal is **raised**, not returned — a write that did not happen must
not read like one that did — and said in French: the day and the value before
the domain is even asked, the validated month and the unknown project caught by
name. The domain stays the authority; this is its reflection, as a locked cell
on the grid is.

### `record_review(project_id: int, note: str, phase?: str)`

**Scope** `updates:write`, and `projects:write` for the phase alone. The weekly
kanban review, said once per project: what was told about it, and where it now
stands.

**One gesture, two use cases, one commit.** A route reaches one use case; this
reaches `PostProjectUpdateUseCase` and `ChangeProjectStatusUseCase`, because
the gesture is one. They share the session the door opened, so the note and the
phase land together or not at all. A tool that posted the note and left the
card would be read as a review that landed; a model asked to chain two calls
lands half of them.

**The second scope is asked for only when a phase is given**, and a key short
of it is refused **before the note is written** — the alternative is a register
saying a project stood still when the meeting said it moved. A key carrying
`updates:write` alone still records reviews, which is the useful minimum.

**A phase is given in the language of the screens.** « construction », not
`development` — though both are accepted, since a client reading the API has
the second in hand. A word that is neither comes back with the six listed: a
model told « invalid enum » guesses again, one handed the list picks. Off-project
work is refused a phase in words, as the domain refuses it.

> Revue consignée sur le projet #13. Phase désormais : construction.

## How a tool speaks

Three rules, carried over from what was already decided about a collector:

- **Facts already worded.** « en retard de 12 jours », never `slippage_days:
  12`. A model handed a number writes the sentence itself, and writes it
  wrong about a third of the time.
- **What is unknown is said.** An absent field is a field a model fills in.
  « Aucune date de mise en service n'est enregistrée » is an answer; silence is
  a fabrication waiting to happen.
- **No identifier a human would not use**, except the ones `find_project`
  hands over for the other tools to consume.

## Deliberately out of V1

- **Staffing a mission, and archiving one.** Both write about something the
  terminal has no business deciding alone: an intervenant names a *person*, and
  `declare_time` already draws the line at writing for somebody else; archiving
  asks what becomes of the work packages, which is a question, not a parameter.
  A screen is built for each.
- **Claude.ai on the web**, which wants OAuth with dynamic registration. Claude
  Code and Desktop take a static header, and that is the whole of Waat.
- **Generating tools from the OpenAPI.** Sixty routes would become sixty tools,
  and a model chaining six calls to answer one question gets three of them
  wrong. A tool is a question somebody asks, never a route.
- **Anything administrative** — minting keys, managing teammates, reopening a
  month. A manager's gestures stay on a screen where they are seen.

## Handing out the keys

A key here belongs to a person, which `ApiKey` already allows: `owner_id` is a
user, and `created_by` is documented as *« the manager who minted it. Not always
the owner »*. Nothing in the code needs changing — but **one sentence of
doctrine does**: `docs/api-keys.md` says a key is attached to a service account
and never to a person. The MCP key is the first assumed exception, and it should
be written there as one rather than left to contradict the page.

What is genuinely awkward is distribution: only a manager mints a key, and the
secret shows once. Fifteen people means fifteen hand-offs. Tolerable to start
with; the real answer, later, is minting one's own MCP key from the screen,
limited to the read scopes.

## Pointing a client at it

Claude Code and Claude Desktop take a static header, which is all Waat needs:

```json
{
  "mcpServers": {
    "ganesh": {
      "type": "http",
      "url": "https://api.ganesh.waat.tools/mcp/",
      "headers": { "Authorization": "Bearer jns_…" }
    }
  }
}
```

The trailing slash is the address; `/mcp` redirects to it. The key is minted in
the « API / MCP » screen by a manager and owned by the person whose terminal it
sits in. `projects:read`, `entries:read`, `audit:read` and `roadmap:read` cover
the reads; add `entries:write` to declare time, and `moods:read` — which no
« Tous » ticks — to read the team's morale.

The same screen's « MCP » tab says all of this to the team, one client at a
time — Claude Code, Codex, Gemini CLI — and hands over the snippet to paste.
The snippets live in `client/src/lib/mcp.ts` rather than inside the tab, and
are read by a test: a configuration somebody pastes into their shell is
exactly the kind of text that goes stale in silence. **What the tab lists is
read from there too**, so a tool added on the server and forgotten on the
screen is a tool nobody knows to ask for.

## How we will know

Three tools, in the hands of three people, for a week. The measure is whether
they are called at all, and which ones.

If nobody calls `what_changed` after a week, the need is not there, and it
should be heard the way the last two were heard — not argued with.
