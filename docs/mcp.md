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
| V1 verbs | **Read only** |

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
writing is out of V1 rather than out forever.

## The three tools

Each is `src/mcp/tools/<name>.py`, and each answers in sentences built through
`src/mcp/tools/say.py` — « 1,5 jour », « 08/09 », « septembre 2026 ». A number
handed over raw is a number a model words itself, and words wrong.

### `find_project(query: str)`

**Scope** `projects:read`. The resolver the other two lean on, and the reason a
model stops inventing identifiers.

Takes what a person would say — « waatcher », « le catalogue » — and returns the
few missions that match, each with its identifier, its kind, its phase and
whether it is still one to book against. Several matches are returned as
several; the choice is the caller's, and a tool that picked one would be
guessing.

> Trois projets portent ce nom. WAATcher (projet, en construction), WAATcher —
> Supervision (lot de WAATcher, en service), WAATcher V1 (archivé le 12 mars).

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

### `what_changed(project: str, since?: str)`

**Scope** `audit:read`. `ListProjectAuditLogUseCase`, over a window that opens
a fortnight back when nobody says otherwise — which is the span somebody coming
back from leave is asking about.

This is the one angle that survived two framings: **nobody knows the projects
they are not on.** Asked after a fortnight away, or on a Monday about a
portfolio one does not follow.

It reads the project's log — which holds everything carrying its `project_id`,
declared time included — and returns a **delta**, not a digest: what changed
phase, what was posted on the thread, how much time went in and by how many
people. A month of raw log lines would be the summary that was dropped the
first time round.

It names four gestures and **counts** the rest (« et 12 autres gestes, que le
Journal du projet détaille »). That is what keeps the French wording here from
becoming a second copy of `client/src/lib/audit-log.ts`: two interfaces each
say the domain's vocabulary in French, and this one only ever learns the four
words it uses.

> Depuis le 1er septembre : passé de cadrage à construction le 8. Quatre
> personnes y ont déclaré 23 jours. Deux mises à jour postées, la dernière le
> 16. L'estimation n'a pas bougé.

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

- **Every write.** `declare_time` is the tool with the most value and the most
  to break: it needs an `entries:write` scope that does not exist, and four
  refusals — validated month, non-working day, value other than 0.5/1.0, a day
  totalling over 1 — each rendered as a sentence. It comes once the three reads
  have proved someone calls them.
- **The moods.** Worth doing, and not like this: an aggregate with no names, no
  identifiers, and a participation floor, behind a `moods:read` scope of its
  own that `all:read` does not cover. The team screen names everyone, but it
  never aggregates *one person over time*, which is precisely what a model
  would do if handed the names. Announced to the team before it ships, never
  discovered afterwards.
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
the « API / MCP » screen by a manager, carries `projects:read`, `entries:read`
and `audit:read`, and is owned by the person whose terminal it sits in.

The same screen's « MCP » tab says all of this to the team, one client at a
time — Claude Code, Codex, Gemini CLI — and hands over the snippet to paste.
The snippets live in `client/src/lib/mcp.ts` rather than inside the tab, and
are read by a test: a configuration somebody pastes into their shell is
exactly the kind of text that goes stale in silence.

## How we will know

Three tools, in the hands of three people, for a week. The measure is whether
they are called at all, and which ones.

If nobody calls `what_changed` after a week, the need is not there, and it
should be heard the way the last two were heard — not argued with.
