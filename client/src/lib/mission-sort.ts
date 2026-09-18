import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { PRIORITIES, phaseRank } from "@/lib/board";

/** The reference list columns the list can be ordered by. */
export type SortColumn =
  "project" | "phase" | "priority" | "category" | "estimated" | "delivered";

export type SortDirection = "asc" | "desc";

/** The column asked for, or `null` for the reference list's own order. */
export interface MissionSort {
  column: SortColumn | null;
  direction: SortDirection;
}

export const NO_SORT: MissionSort = { column: null, direction: "asc" };

const COLUMNS: SortColumn[] = [
  "project",
  "phase",
  "priority",
  "category",
  "estimated",
  "delivered",
];

const PARAMETERS = { column: "sort", direction: "direction" } as const;

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
  estimated: (m) => m.project.estimated_days ?? null,
  delivered: (m) => m.delivered_days,
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
  const sign = sorted.direction === "desc" ? -1 : 1;

  return (a: Mission, b: Mission): number => {
    const left = valueOf(a);
    const right = valueOf(b);

    if (left === null || right === null) {
      if (left === right) return byLabel(a, b);
      return left === null ? 1 : -1;
    }

    const gap =
      typeof left === "string" && typeof right === "string"
        ? left.localeCompare(right, "fr")
        : Number(left) - Number(right);

    return gap !== 0 ? sign * gap : byLabel(a, b);
  };
}

/**
 * The sort you get by clicking a column: ascending, descending, then nothing.
 * The third click gives the reference list its own order back, without having
 * to hunt for how to find it again.
 */
export function nextSort(sorted: MissionSort, column: SortColumn): MissionSort {
  if (sorted.column !== column) return { column, direction: "asc" };
  if (sorted.direction === "asc") return { column, direction: "desc" };
  return NO_SORT;
}

export function readSort(params: URLSearchParams): MissionSort {
  const column = params.get(PARAMETERS.column);
  if (!column || !COLUMNS.includes(column as SortColumn)) return NO_SORT;

  return {
    column: column as SortColumn,
    direction: params.get(PARAMETERS.direction) === "desc" ? "desc" : "asc",
  };
}

/** Writes the sort into the URL, leaving the other parameters alone. */
export function writeSort(params: URLSearchParams, sorted: MissionSort): void {
  params.delete(PARAMETERS.column);
  params.delete(PARAMETERS.direction);
  if (sorted.column === null) return;

  params.set(PARAMETERS.column, sorted.column);
  params.set(PARAMETERS.direction, sorted.direction);
}
