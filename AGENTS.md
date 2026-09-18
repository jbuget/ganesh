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
