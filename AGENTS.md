<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `client/node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# UI conventions

## Component architecture — Atomic Design

Front-end components are organised in strict levels under
`client/src/components/`:

```
ui/          External primitives (shadcn/ui). Treated as dependencies, never
             edited by hand.
atoms/       Building blocks, with no dependency on another local component.
             e.g. DayCell, DayHeader, DayTotalCell, TotalCell, MissionLabel,
             MissionSelector, PriorityMark, CategoryMark, FilterSelect
molecules/   Atoms assembled into one functional unit.
             e.g. MissionRow, MissionFilters, ProjectCard, BoardColumn
organisms/   Complex sections made of molecules and atoms. An organism may
             compose another: a page assembles sections.
             e.g. TimesheetGrid, TimesheetPage, BoardPage, ProjectsPage
             (templates = Next.js layout.tsx / pages = app/)
```

**Rules:**
- An atom never imports another local component (`ui/` and `lib/` aside). What
  classifies a component is its dependencies, not how complex it looks.
- A molecule imports atoms only.
- An organism may import atoms, molecules and other organisms.
- Pages (`app/`) import organisms only.
- A screen's logic (state, data, writes) lives in a hook under `src/lib/`, not
  in the component: the component carries the rendering alone.
- Every new component must be placed at the right level before being used.
- Never create a `shared/`, `common/`, `features/` or any other folder outside
  this structure.

These rules are **enforced by `eslint-plugin-boundaries`**
(`client/eslint.config.mjs`): a violation is a lint error, not a review
remark. Colocated test files are exempt.

## Components and files

- One component per file, named in `PascalCase.tsx`, matching the component
  name.
- Colocated test: `MyComponent.test.tsx` beside `MyComponent.tsx`.

## Cursor

Every clickable element (`<button>`, `<a>`, anything with `onClick`) must carry
the `cursor-pointer` class.

## Language: code in English, interface in French

The codebase is entirely in English — identifiers, comments, test labels,
database columns and API fields. **What the user reads stays in French**: screen
labels, phase names, column headings, dialog text.

Two consequences worth knowing:

- An English comment quoting the interface quotes French, and that is right.
- A rename must never cross a label. A French label composed at run time —
  `` `${count > 1 ? "mises à jour" : "mise à jour"}` `` — is invisible to the
  type checker and to the tests, which assert on the count rather than the
  wording. Only opening the screen catches it. Check in the browser after any
  broad rename.

## Tables

Every table of the application is drawn in the **same frame**, and a new one
does not get to invent its own. It is described in `client/src/lib/table-frame.ts`:

```tsx
<Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
  <TableHeader className={TABLE_HEADER}>
    <TableRow>
      <TableHead className={STRONG_SEPARATOR}>Ce qui nomme la ligne</TableHead>
      …
```

- `TABLE_FRAME` — the strong rule around, the faint lines within. Drawn by the
  cells at the edges, never by the table itself.
- `TABLE_HEADER` — the band of titles, white, pinned, closed by a strong rule.
- `STRONG_SEPARATOR` — closes the column that **names** the row, off from those
  that describe it.

The row takes the page's tint (`bg-slate-50 hover:bg-slate-100`) and the naming
cell stays white, one step behind on hover: the subject of the line reads as its
anchor rather than as its first column. `MissionsTable`, `UsersTable` and
`ApiKeysTable` all read this way — two tables that read alike must not be able
to drift apart.

Wrap the table in
`<div className="[&_[data-slot=table-container]]:overflow-visible">`: the shadcn
container otherwise opens a scrolling context that would hold the pinned header
inside the table.

**The strong rule is `STRONG_RULE`, and it binds outside `<table>` too.** A
screen that draws its own frame in plain elements — the roadmap does, its rows
being bars rather than cells — still closes it at that weight, and never at
`slate-300`. Strength marks an edge: the frame around, and any line that breaks
the reading in two, such as the title of a band, which carries it above and
below. What merely separates two rows stays faint. A frame drawn a shade
lighter than the tables beside it reads as a different, weaker object, which is
exactly what the shared grammar exists to prevent.

## One visual grammar

Phase, priority and category all read the same way: **a coloured mark, then a
label in ordinary text**. No filled surfaces — colour marks, it does not fill.

Each mark carries a distinct shape, so two marks on one line never read as the
same information: the phase is a round dot, the priority a signal gauge, the
category a square bullet. Shape also carries the priority scale on its own,
which keeps it readable for whoever cannot tell the colours apart.

## Entry grid

- Non-working days (weekends and public holidays) are visually distinct and
  recognisable at a glance.
- Future days show dimmed: they are forecast, not delivered.
- Totals always tell **delivered** from **forecast**.
- A validated month shows read-only, stating who validated it and when.
