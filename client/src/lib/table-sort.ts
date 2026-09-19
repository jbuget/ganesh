/**
 * Ordering a table by one of its columns.
 *
 * The mission reference list and the team list are arranged the same way: one
 * clicks a title, the column takes over, a third click gives the list its own
 * order back. Only the columns and what they compare differ from one screen to
 * the next — the cycle, the address and the way a tie is read are shared, and
 * are written here once.
 */

export type SortDirection = "asc" | "desc";

/** The column asked for, or `null` for the list's own order. */
export interface ColumnSort<Column extends string> {
  column: Column | null;
  direction: SortDirection;
}

/** No column asked for: the list keeps the order it gives itself. */
export const NO_COLUMN_SORT = { column: null, direction: "asc" } as const;

const PARAMETERS = { column: "sort", direction: "direction" } as const;

/**
 * The sort you get by clicking a column: ascending, descending, then nothing.
 * The third click gives the list its own order back, without having to hunt for
 * how to find it again.
 */
export function nextColumnSort<Column extends string>(
  sorted: ColumnSort<Column>,
  column: Column,
): ColumnSort<Column> {
  if (sorted.column !== column) return { column, direction: "asc" };
  if (sorted.direction === "asc") return { column, direction: "desc" };
  return NO_COLUMN_SORT;
}

/**
 * The sort as the URL carries it.
 *
 * An unknown column is ignored: a mistyped address must show the list, not an
 * empty screen with no explanation.
 */
export function readColumnSort<Column extends string>(
  params: URLSearchParams,
  columns: readonly Column[],
): ColumnSort<Column> {
  const column = params.get(PARAMETERS.column);
  if (!column || !columns.includes(column as Column)) return NO_COLUMN_SORT;

  return {
    column: column as Column,
    direction: params.get(PARAMETERS.direction) === "desc" ? "desc" : "asc",
  };
}

/** Writes the sort into the URL, leaving the other parameters alone. */
export function writeColumnSort<Column extends string>(
  params: URLSearchParams,
  sorted: ColumnSort<Column>,
): void {
  params.delete(PARAMETERS.column);
  params.delete(PARAMETERS.direction);
  if (sorted.column === null) return;

  params.set(PARAMETERS.column, sorted.column);
  params.set(PARAMETERS.direction, sorted.direction);
}

/**
 * Compares two rows on the value a column gives.
 *
 * A missing value does not compare: it goes to the end of the list whichever
 * way round the sort is, rather than being given a rank it does not have.
 * Otherwise reversing the direction would bring the gaps to the top.
 *
 * Ties are settled by the caller's own tie-breaker — the name, everywhere so
 * far — so that two rows a column cannot separate keep a stable order from one
 * render to the next.
 */
export function compareValues<Row>(
  left: Row,
  right: Row,
  valueOf: (row: Row) => string | number | null,
  direction: SortDirection,
  tieBreaker: (a: Row, b: Row) => number,
): number {
  const first = valueOf(left);
  const second = valueOf(right);

  if (first === null || second === null) {
    if (first === second) return tieBreaker(left, right);
    return first === null ? 1 : -1;
  }

  const gap =
    typeof first === "string" && typeof second === "string"
      ? first.localeCompare(second, "fr")
      : Number(first) - Number(second);

  if (gap === 0) return tieBreaker(left, right);
  return direction === "desc" ? -gap : gap;
}
