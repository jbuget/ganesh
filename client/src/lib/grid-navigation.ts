/**
 * Moving around the entry grid with the keys.
 *
 * A month with a dozen missions on it is a few hundred cells, and reaching one
 * of them with the mouse is the whole cost of filling a month in. The keys
 * answer that: the arrows walk the grid as a spreadsheet's do, one day to the
 * right, one mission down.
 *
 * The rule the whole thing rests on: **the focus only ever lands where one may
 * write.** A closed day is stepped over rather than stopped on — it takes no
 * entry, so pausing there would only cost a keystroke. The same goes for a
 * validated month, where nothing is open and the arrows therefore do nothing:
 * there is nothing to move between.
 *
 * Nothing wraps. At the end of a row the arrow answers nothing and the focus
 * stays where it was, which is what a spreadsheet does and what the hand
 * expects: a cursor that jumped to the next mission would lose whoever was
 * running along a week.
 */

/** One cell of the grid: a mission, a day. */
export interface GridCell {
  projectId: number;
  day: string;
}

/** The keys that move the focus. Anything else is left to the cell. */
export type NavigationKey =
  "ArrowUp" | "ArrowDown" | "ArrowLeft" | "ArrowRight" | "Home" | "End";

const NAVIGATION_KEYS: readonly string[] = [
  "ArrowUp",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "Home",
  "End",
];

/** Whether a key moves the focus, which is what decides if the grid takes it. */
export function isNavigationKey(key: string): key is NavigationKey {
  return NAVIGATION_KEYS.includes(key);
}

/**
 * How a cell is named in the DOM, so that the grid can find it back.
 *
 * The keys are handled once, on the table, rather than cell by cell: three
 * hundred handlers and three hundred refs to move one focus is a price paid on
 * every render. What the table gets from the event is this string, and that is
 * enough to know which cell was left and to find the one to land on.
 */
export function cellId(cell: GridCell): string {
  return `${cell.projectId}:${cell.day}`;
}

/** The cell a `data-cell` names, or `null` when it names nothing. */
export function parseCellId(id: string | undefined): GridCell | null {
  if (!id) return null;
  const [projectId, day] = id.split(":");
  const parsed = Number(projectId);
  return Number.isNaN(parsed) || !day ? null : { projectId: parsed, day };
}

/** The grid as moving around it needs to know it: its axes, and what is open. */
export interface NavigableGrid {
  /** Mission ids, in the order the rows are drawn. */
  rows: number[];
  /** Days, in the order the columns are drawn. */
  days: string[];
  /** Whether a cell can take the focus, which is to say whether it takes an entry. */
  isOpen: (cell: GridCell) => boolean;
}

/**
 * The cell a key moves to, or `null` when there is nowhere to go.
 *
 * `null` covers the edge of the grid, a column closed all the way down, and a
 * cell the grid does not hold — a row removed under the hand, say. All three
 * mean the same thing to the caller: leave the focus where it is.
 */
export function nextCell(
  grid: NavigableGrid,
  from: GridCell,
  key: NavigationKey,
): GridCell | null {
  const rowIndex = grid.rows.indexOf(from.projectId);
  const dayIndex = grid.days.indexOf(from.day);
  if (rowIndex === -1 || dayIndex === -1) return null;

  switch (key) {
    case "ArrowRight":
      return alongRow(grid, rowIndex, dayIndex + 1, 1);
    case "ArrowLeft":
      return alongRow(grid, rowIndex, dayIndex - 1, -1);
    case "Home":
      return alongRow(grid, rowIndex, 0, 1);
    case "End":
      return alongRow(grid, rowIndex, grid.days.length - 1, -1);
    case "ArrowDown":
      return downColumn(grid, rowIndex + 1, dayIndex, 1);
    case "ArrowUp":
      return downColumn(grid, rowIndex - 1, dayIndex, -1);
  }
}

/** The first open cell from `dayIndex`, walking the row in `step`'s direction. */
function alongRow(
  grid: NavigableGrid,
  rowIndex: number,
  dayIndex: number,
  step: 1 | -1,
): GridCell | null {
  for (let index = dayIndex; index >= 0 && index < grid.days.length; index += step) {
    const cell = { projectId: grid.rows[rowIndex], day: grid.days[index] };
    if (grid.isOpen(cell)) return cell;
  }
  return null;
}

/** The first open cell from `rowIndex`, walking the column in `step`'s direction. */
function downColumn(
  grid: NavigableGrid,
  rowIndex: number,
  dayIndex: number,
  step: 1 | -1,
): GridCell | null {
  for (let index = rowIndex; index >= 0 && index < grid.rows.length; index += step) {
    const cell = { projectId: grid.rows[index], day: grid.days[dayIndex] };
    if (grid.isOpen(cell)) return cell;
  }
  return null;
}

/**
 * The one cell of the grid that Tab reaches.
 *
 * A grid holds a single stop, and it follows the focus: tabbing through three
 * hundred cells to reach what comes after them is not navigation. The cursor
 * is where the hand last was; before anybody has touched the grid — and
 * whenever the cursor no longer names a cell the grid holds, a mission removed
 * under the hand — the stop falls back to the first cell one may write on, so
 * that Tab always has somewhere to land.
 */
export function tabStop(grid: NavigableGrid, cursor: GridCell | null): GridCell | null {
  if (cursor && holds(grid, cursor) && grid.isOpen(cursor)) return cursor;
  return firstOpen(grid);
}

function holds(grid: NavigableGrid, cell: GridCell): boolean {
  return grid.rows.includes(cell.projectId) && grid.days.includes(cell.day);
}

/** The first cell one may write on, read row by row. `null` when none is. */
function firstOpen(grid: NavigableGrid): GridCell | null {
  for (const projectId of grid.rows) {
    for (const day of grid.days) {
      const cell = { projectId, day };
      if (grid.isOpen(cell)) return cell;
    }
  }
  return null;
}
