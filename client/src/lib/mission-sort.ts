import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { PRIORITIES, phaseRank } from "@/lib/board";
import {
  NO_COLUMN_SORT,
  compareValues,
  nextColumnSort,
  readColumnSort,
  writeColumnSort,
  type ColumnSort,
  type SortDirection,
} from "@/lib/table-sort";

export type { SortDirection };

/** The reference list columns the list can be ordered by. */
export type SortColumn =
  "project" | "phase" | "priority" | "category" | "build" | "run";

/** The column asked for, or `null` for the reference list's own order. */
export type MissionSort = ColumnSort<SortColumn>;

export const NO_SORT: MissionSort = NO_COLUMN_SORT;

const COLUMNS: SortColumn[] = [
  "project",
  "phase",
  "priority",
  "category",
  "build",
  "run",
];

const PRIORITY_RANKS = new Map(PRIORITIES.map((p, rank) => [p.value, rank]));

type Mission = ProjectListItemResponse;

/**
 * What each column gives to compare.
 *
 * A missing value is `null`: it does not compare, and the sort puts it at the
 * end of the list rather than inventing a rank for it.
 */
const VALUES: Record<SortColumn, (m: Mission) => string | number | null> = {
  project: (m) => m.project.label,
  phase: (m) => (m.project.status ? phaseRank(m.project.status) : null),
  priority: (m) =>
    m.project.priority ? (PRIORITY_RANKS.get(m.project.priority) ?? null) : null,
  category: (m) => m.project.category,
  // Sorting reads what the row shows: a folded parent carries its work
  // packages, so the tree is what gets compared.
  build: (m) => m.tree_cost.build_days || null,
  run: (m) => m.tree_cost.run_days || null,
};

function byLabel(a: Mission, b: Mission): number {
  return a.project.label.localeCompare(b.project.label, "fr");
}

/**
 * Where the mission stands first, its name second.
 *
 * The reference list is scanned the way the kanban reads, left to right: what
 * is starting at the top, what is running at the bottom. At equal phase, the
 * alphabet, the only order in which one finds a mission one knows by name.
 */
function byPhaseThenLabel(a: Mission, b: Mission): number {
  const gap = phaseRank(a.project.status) - phaseRank(b.project.status);
  return gap !== 0 ? gap : byLabel(a, b);
}

/**
 * The comparator to apply to missions of the same level.
 *
 * The direction only reverses the comparison of values: missions without a
 * value stay at the end of the list, and two missions a column ties are still
 * settled by their name. Without that, reversing the direction would bring the
 * gaps to the top, and the order of ties would change on every render.
 */
export function sortComparator(sorted: MissionSort) {
  if (sorted.column === null) return byPhaseThenLabel;

  const valueOf = VALUES[sorted.column];

  return (a: Mission, b: Mission): number =>
    compareValues(a, b, valueOf, sorted.direction, byLabel);
}

/**
 * The sort you get by clicking a column: ascending, descending, then nothing.
 * The third click gives the reference list its own order back, without having
 * to hunt for how to find it again.
 */
export function nextSort(sorted: MissionSort, column: SortColumn): MissionSort {
  return nextColumnSort(sorted, column);
}

export function readSort(params: URLSearchParams): MissionSort {
  return readColumnSort(params, COLUMNS);
}

/** Writes the sort into the URL, leaving the other parameters alone. */
export function writeSort(params: URLSearchParams, sorted: MissionSort): void {
  writeColumnSort(params, sorted);
}
