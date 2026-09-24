# Reminders by mail (V1)

> **Built.** This was the design brief; it is now the reference for what
> shipped — the cadence on `users`, the letter in `modules/notifications`, the
> clock in `src/scheduler/`. *Out of scope for V1* still says what was left out
> on purpose.

## The gap it closes

The bell works. It only works for somebody who has Ganesh open, which is most
of the team almost never: a mention waits until the next visit, and a month
reopened on Friday is found on Monday.

Two other tuyaux were weighed and set aside, and `docs/teams.md` holds the
reasoning: browser push asks each person for a permission they refuse by
reflex, and a Teams app is gated on two consents only an administrator can
give. Mail asks nobody for anything. Mailgun already answers, over SMTP, on a
domain the team holds.

The finding that decided the shape: **the problem is « not seen », not « not
seen fast »**. Nobody needs to learn within thirty seconds that they were
mentioned. One letter a day, naming what is waiting, closes the gap without
interrupting anybody — and without a channel that has to be live.

## Decisions taken

| Question | Decision |
|---|---|
| What goes out | **One letter summing up what is waiting**, never one per notification |
| How often | **The reader chooses**: every day, every week, or never |
| Where the choice is made | A **profile page**, reached from one's own name at the foot of the sidebar |
| Default | **Every day.** « Never » by default would fix nothing |
| What it contains | One line per kind, with a count, and one link to the inbox |
| What it repeats | **Nothing.** Only what arrived since the last letter |
| Transport | **SMTP**, behind a `Mailer` port. Mailgun today, anything tomorrow |
| Where the French lives | On the server, in the domain, under test. The one exception, and it is argued below |
| The clock | **Inside the application**, an `asyncio` task in the lifespan |
| What makes it safe | A **claim row in PostgreSQL**. The number of processes stops mattering |
| Read state | **Untouched.** Reading the letter is not reading the inbox |
| Traced | The **choice** is, like a presence. The **sending** is not |

## Why a digest, and not one mail per line

One mail per notification would be hated within a week, and the way people say
so is a rule in Outlook. A filter is silent, permanent, and it takes the bell
down with it — the reader stops seeing even the letter that mattered. That is
the failure this feature exists to fix, reproduced and made worse.

So the letter is rare, short, and **never empty**. A letter that arrives
saying nothing teaches the reader that it can be ignored, and the next one is
too.

Its job is not to carry the news. Its job is to get somebody to open the
inbox, where the news already is and where the read state lives. **It points;
it does not copy.** That is what lets it stay three lines long.

## Where it lives

Inside `notifications`. The bell and the letter are two readings of one inbox,
and a module of its own would have to reach into this one for everything it
holds.

Nothing of the write path moves. The letter **reads** the notifications table
on a clock; `deliver()`, the fan-out and the folding of repeats are untouched,
and cannot be broken by any of this.

```
modules/notifications/
  domain/entities/reminder.py            Reminder, ReminderLine
  domain/entities/letter.py              Letter — to, subject, text, html
  domain/repositories/mailer.py          Mailer (port)
  domain/services/roundup.py             Grouping, and the « never empty » rule
  domain/services/reminder_letter.py     The French. Pure, and under test
  application/use_cases/send_due_reminders.py
  infrastructure/mail/smtp_mailer.py     Mailgun, MailPit, anything with SMTP
```

The cadence itself is a fact about a person, so it sits on `User` beside the
declared week — `reminder_cadence`, a column on `users`, not a table of its
own.

## What the mail says, and why the French is on the server

Everywhere else, what the reader reads is composed by the interface:
`client/src/lib/notifications.ts` turns `project.assigned` into a French
sentence, and it is under test because a notification nobody can read is not
one. A letter has no browser in the loop, so that table cannot serve it.

The resolution is not to copy the sentences but to **need much less of them**.
The letter groups by kind and counts:

```
Objet : Ganesh — 3 choses vous attendent

  2 mentions
  1 mois rouvert

  Ouvrir : https://ganesh.waat.tools/notifications
```

One French noun per kind, singular and plural, and nothing composed. It lives
in `domain/services/reminder_letter.py`, and a test asserts that **every
`NotificationKind` has one** — a kind added tomorrow cannot silently render a
blank line. The same discipline as the wording table it does not share.

The letter goes out as `multipart/alternative`: a text part that says all of
the above, and an HTML part that says it again with a link. Plain on purpose —
HTML mail that survives Outlook is a craft of its own, and a letter this short
gains nothing from it.

## The cadence, and where it is chosen

Three values, in the domain, on the user:

| | |
|---|---|
| `DAILY` | One letter a working day, if anything arrived |
| `WEEKLY` | One letter on the first working day of the week |
| `NEVER` | Nothing |

**`NEVER` is not optional.** Without a way out that Ganesh can see, people
leave by writing a mail rule, and then nobody knows they left. An opt-out one
can read is worth more than a silence one cannot.

**The default is `DAILY`**, including for everybody already provisioned. A
default of `NEVER` would fix nothing: nobody goes looking for a setting they
have not felt the need for. This is a feature that arrives in people's
mailboxes unasked, so — as for `team_mood` — **tell the team before it starts
arriving**, not after.

The choice is made on a profile page of one's own, reached from the menu
behind one's name at the foot of the sidebar. The route carries no teammate,
and that is the guarantee rather than a shorthand: as with `PUT
/users/me/presence`, there is no colleague's cadence it could reach.

Choosing is traced in `audit_log`, like declaring a week. Sending is not: a
letter is a channel, not a gesture — the same reason a sign-in and a reaction
stay out of it.

## Never the same thing twice

A letter that listed everything unread would list the same lines every morning
until the reader gave in, which is one more way of teaching them to filter it.

So each person carries `reminder_sent_at`, and a letter holds **what arrived
after it and is still unread**. Read in the application in the meantime, and
it is not in the letter; ignored, and it is not in the next one either — the
bell still has it, which is where it belongs.

The stamp moves only when a letter actually went out. Nothing sent, nothing
moved, and the next run considers the same window.

## The clock

An `asyncio` task started in the application's lifespan — the same lifespan
the MCP server already needs. No external brick, nothing to reproduce on a
laptop, and `make run` gives the production behaviour.

It lives in `src/scheduler/`, a top-level package beside `src/mcp/` and for
the same reason: it crosses modules and is reached by none. It is a **third
way in** — the routers answer a request, the tools answer a sentence, this one
answers a clock — and two `import-linter` contracts hold it there, exactly as
they hold `src.mcp`: nothing imports it but `src.main`, and it names no
repository of its own.

### The one thing that would go wrong

The API runs as a single `uvicorn` process today (`server/Dockerfile`), so an
in-process task fires once. `--workers 4` is one word away, it is the obvious
first optimisation the day the host feels slow, and a naive scheduler would
then send four letters to everybody — silently, and only in production.

So the number of processes is made not to matter:

```sql
scheduled_run(job text, due_on date, claimed_at timestamptz)   -- PK (job, due_on)
-- job reads "reminder:daily" or "reminder:weekly": two rounds on one day
-- are two claims, never one.
```

Each tick tries an `INSERT … ON CONFLICT DO NOTHING`. Whoever inserted works;
the others go back to sleep. **The uniqueness constraint is the lock** — and
it buys idempotence for free: a deploy at 9 h does not re-send the letter of
8 h 30, and neither does a crash-restart.

The table carries a `job` column rather than being named after the one job
there is. It is one column, and it is what makes the claim mean « this run, on
this day » instead of « the reminder, on this day ».

### What the tick decides

Every five minutes, in **Europe/Paris** — hard-coded, as the public holidays
are hard-coded to France, and for the same reason: this is one team, in one
country, and a timezone in the configuration would be a setting nobody ever
sets correctly. Read in UTC, « 8 h 30 » drifts by an hour twice a year.

- Past the send time, and **today is a working day** — `classify_day()`, the
  calendar module's, the one the grid already uses. A letter on 15 August is
  noise.
- `DAILY` is due every working day. `WEEKLY` is due on the **first working day
  of the week**, which is not « Monday »: the week Monday is a holiday, the
  letter goes out on the Tuesday rather than not at all.

## Sending, and failing

**Two kinds of failure, and telling them apart is what the `Mailer` port is
for.** They are not handled alike, and treating them alike is what makes a
feature go dark without anybody noticing.

**One reader's letter refused** — an address that no longer exists, a mailbox
that is full — is that letter lost, and the round carries on. The stamp does
not move for whoever was not written to, so the next run considers the same
window again. That is the only retry there is, and it is enough: no queue, no
outbox, and what the letter announced is still in the inbox.

**Nowhere to post at all** — a key Mailgun refuses, a host nobody can reach —
is not that. Every letter of the round would meet the same wall, so:

- the adapter raises `MailerUnavailableError` rather than one exception per
  recipient;
- the round **stops where it is**, and whoever was already written to keeps
  their stamp, so the retry writes to the rest and to nobody twice. That last
  part is not free: both callers commit **on the way out, failure included**,
  because a stamp rolled back is a letter sent twice. In memory it is free and
  no unit test can see it, which is why one integration test pins it against a
  real database;
- the clock says it once, as a sentence rather than fifteen stack traces, and
  **gives the run back** — `release()` deletes the claim, so the next tick
  retries. Without that, the claim being taken before the work means a key
  refused at 8 h 30 and fixed at 9 h still costs the whole day.

**An unconfigured mailer refuses too**, and that is the point rather than an
oversight. The clock never starts without a host, so the only caller that can
reach an unconfigured mailer is a manager pressing « envoyer » — usually to
find out whether the configuration works. Dropping the letter and answering
« envoyée » would tell them it does, send nothing, and move every stamp it
touched: what it announced would never be announced again.

**Without SMTP configured the clock does not start**, and says so in the log.
Same contract as `GEMINI_API_KEY`: a laptop with no mail server runs the whole
application and nothing is broken. `docker-compose.yml` has a MailPit beside
the MinIO that already stands in for S3 — one adapter, two addresses, and
letters you can read locally without sending anything to anybody.

## The round a manager sends by hand

`POST /notifications/reminders/run`, naming the cadence. It exists for two
mornings: the one the clock got wrong, and the first one — seeing a real
letter before trusting the whole thing to a schedule.

- **It answers to no clock.** No send time, no working day: the manager
  decided.
- **It takes no claim**, and that is deliberate. A run that respected the
  day's claim would do nothing at all after a failed morning, which is the one
  moment it exists for. Nothing is sent twice for it: `reminder_sent_at` moves
  as each letter goes, so a second press writes only to whoever has something
  new. Two managers pressing within the same second could double-write to one
  reader; the window closes on the first stamp, and that is judged small
  enough to name rather than to engineer around.
- **Managers only**, and the rule lives in the use case rather than on the
  route alone: it writes to the whole team at once, and a second way in — a
  tool, a script — must meet the same wall.
- **It is traced**, where the clock's round is not. A letter is a channel; a
  manager sending one deliberately is a gesture, as generating a numéro of La
  Gazette is. The line carries the cadence and how many letters went out,
  including zero — « j'ai lancé la campagne et rien n'est parti » is exactly
  what one opens the register for.
- It answers **503** when there is nowhere to post, which is the answer worth
  having when one is testing the configuration: it is not the caller's request
  that is wrong. `ServiceUnavailableError` is new in `src/shared/`, and
  `status_for` now walks an exception's parents so a module narrowing one of
  these keeps its status instead of falling through to 400.

The button sits at the foot of « Notifications », for managers alone. The
tension is worth naming: that page is *mine*, this writes to *everybody*. It
is kept apart by a rule and a heading rather than moved — the profile is
personal, the teammates screen is about people, and a screen of its own for
one button would be furniture.

## What it never does

- **It never marks anything read.** Receiving a letter is not reading an inbox,
  and a channel that cleared the bell would destroy the only record of what
  somebody has actually seen.
- **It never sends an empty letter.** The rule lives in `roundup()`, which
  returns nothing rather than a `Reminder` with no lines.
- **It never writes to `audit_log`.** Choosing a cadence does; sending does
  not.
- **It never reaches an inactive account**, nor one that said `NEVER`.
- **It never carries what an update said.** A subject line is read on a lock
  screen and over a shoulder: the letter names kinds and counts, never the
  text somebody wrote.

## Configuration

All empty by default, all optional. Nothing here is required to run Ganesh.

```python
smtp_host: str = ""                  # Mailgun in production, MailPit locally
smtp_port: int = 587
smtp_username: str = ""
smtp_password: str = ""              # Parameter Store in production
smtp_starttls: bool = True
mail_from: str = "Ganesh <notifications@ganesh.waat.tools>"
web_url: str = "http://localhost:3000"   # what the letter links to
reminder_send_at: str = "08:30"          # Europe/Paris
reminder_tick_seconds: int = 300
```

`web_url` is new, and the API had no notion of the client's address before
this: `api_url` is its own. The letter is the first thing Ganesh writes that
has to point back at a screen.

## Out of scope for V1

Each of these is a decision rather than an omission, and each would be a small
addition on top of what is built:

- **Naming the projects concerned.** « 2 mentions » rather than « 2 mentions,
  sur Refonte du site ». The obvious next step, left out to keep the first
  letter one thing done properly.
- **Any other cadence.** No « immediately », which would be one mail per line
  under another name, and no digest at an hour each person picks.
- **Any other letter.** No welcome, no month-end nudge, no manager report.
  The one thing that goes out is what is already waiting in an inbox.
- **A retry queue, an outbox, a bounce webhook.** Mailgun records what it
  could not deliver; Ganesh does not need to.
- **Unsubscribe by link.** The preference is one click away behind one's own
  name, on a tool one is signed into. A token in a URL would be a second way
  in to build and to protect.

## Files that matter

| File | What |
|---|---|
| `server/src/modules/users/domain/entities/reminder_cadence.py` | The three values |
| `server/src/modules/users/application/use_cases/choose_own_reminder_cadence.py` | Saying which |
| `server/src/modules/notifications/domain/entities/reminder.py` | What is waiting, by kind |
| `server/src/modules/notifications/domain/services/roundup.py` | Grouping, and « never empty » |
| `server/src/modules/notifications/domain/services/reminder_letter.py` | The French, under test |
| `server/src/modules/notifications/domain/repositories/mailer.py` | The port, and the two kinds of failure |
| `server/src/modules/notifications/infrastructure/mail/smtp_mailer.py` | The adapter |
| `server/src/modules/notifications/application/use_cases/send_due_reminders.py` | One cadence, one run |
| `server/src/scheduler/due.py` | What is owed, read off a clock |
| `server/src/scheduler/claim.py` | The lock, the ledger, and giving a run back |
| `server/src/scheduler/clock.py` | The loop |
| `server/src/scheduler/wiring.py` | Where it gets a session and a round |
| `client/src/components/organisms/ProfilePage.tsx` | Where one chooses |
| `client/src/lib/reminders.ts` | The three cadences, in French |
| `client/src/components/atoms/RunRemindersPanel.tsx` | Where a manager sends one by hand |
| `client/src/components/atoms/UserMenu.tsx` | How one gets there |
