# Monday ↔ Janus mapping (groundwork for V1.1)

> V1 does **not** talk to Monday. This document prepares V1.1: a "Synchroniser
> vers Monday" button, managers only, write-only.

Monday column titles, group names and status values are quoted as they read on
the board, in French: they identify real objects and must match exactly.

## Source

- Account: `waat-global`, Pro plan
- Board **Projets Dev & Automatisation**: `5091544837`
  ([link](https://waat-global.monday.com/boards/5091544837))
- Workspace: "Chantiers UC IA & Dev" (`4420418`)
- Subitem board (work packages): `5091588527`
- Groups: `topics` ("Backlog"), `group_mm0fqn9k` ("Hors pipe")

## Columns

### Project level (item on board `5091544837`)

| Column | ID | Type | Use |
|---|---|---|---|
| Tps estimé dev (j) | `numeric_mm0e80ek` | numbers | read → `projects.estimated_days` |
| **Tps passé (j)** | `numeric_mm1zyga2` | numbers | **write** ← sum of what was delivered |
| Statut d'avancement | `color_mm0e7asn` | status | filters which projects can be synced |
| Développeur(s) | `text_mm0f5bwg` | text | ⚠️ free text, unusable as a key |
| Subitems | `subtasks_mm0ej7ty` | subtasks | access to the work packages |

### Work package level (subitem, board `5091588527`)

| Column | ID | Type | Use |
|---|---|---|---|
| Tps estimé dev | `numeric_mm6afd76` | numbers | read → `projects.estimated_days` |
| **Tps passé dev** | `numeric_mm6av3hh` | numbers | **write** ← sum of what was delivered |
| Owner | `person` | people | informative |
| Statut | `status` | status | informative |

## Sync rules

1. **One way**: Janus → Monday. A value typed into Monday is overwritten,
   never read back. Monday is not a source of entry.
2. **Delivered only**: sum nothing but the entries whose `day <= today`.
   Forecast must never show up as time spent.
3. **Join keys**: `projects.monday_item_id` (project) and
   `projects.monday_subitem_id` (work package). Monday ids are stable.
4. **Project total** = the sum of its work packages + the entries booked
   straight onto the project.
5. **Never synced**: `off_project` activities (absences, training, internal)
   carry no Monday id.
6. **Scope**: only the projects of the "Backlog" group whose "Statut
   d'avancement" is active (En cours, Prêt à démarrer en dev, POC, Étude).

## Worth watching

Janus's phase statuses (`exploration`, `scoping`, `development`,
`validation`, `deployment`, `operations`) are **distinct** from Monday's "Statut
d'avancement". Neither must overwrite the other: they answer different
questions.
