"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { valueForKey, type DayValue } from "@/lib/day-value";
import {
  cellId,
  isNavigationKey,
  nextCell,
  parseCellId,
  tabStop,
  type GridCell,
  type NavigableGrid,
} from "@/lib/grid-navigation";

/** Writes one cell: what the grid does with an hour somebody typed. */
export type WriteCell = (cell: GridCell, value: DayValue) => void;

/**
 * Everything the keys do to the entry grid: move the focus, and write.
 *
 * Both live here rather than half here and half in the component, because
 * they are one decision taken on one key press — an hour writes, an arrow
 * moves, anything else is left to the browser — and splitting that decision
 * across two files is how a key ends up doing both or neither.
 *
 * **One handler on the table, not one per cell.** A month with a dozen
 * missions on it is a few hundred cells; hanging a handler and a ref on each
 * of them is a price paid on every render to move a single focus. The event
 * bubbles to the table, the cell that fired it says its name through
 * `data-cell`, and the one to land on is found back by that same name. Each
 * cell carries a string and nothing else.
 *
 * `grid` is rebuilt on every render — it closes over what the screen holds —
 * so it is kept in a ref as well: the handlers are made once and still read
 * the grid as it stands, the way `usePendingEntries` keeps its writes.
 */
export function useGridKeys(grid: NavigableGrid, write: WriteCell) {
  // Where the hand last was, which is where Tab comes back to.
  const [cursor, setCursor] = useState<GridCell | null>(null);

  const held = useRef(grid);
  useEffect(() => {
    held.current = grid;
  });

  const writing = useRef(write);
  useEffect(() => {
    writing.current = write;
  });

  const onKeyDown = useCallback((event: React.KeyboardEvent<HTMLElement>) => {
    const from = parseCellId((event.target as HTMLElement).dataset?.cell);
    if (!from) return;

    // The hours are read before the arrows. One types what one reads: the cell
    // shows « 4 » and the key is `4`. An odd hour is refused rather than
    // rounded, and falls through to the browser like any other key.
    const typed = valueForKey(event.key);
    if (typed !== null) {
      // Asked rather than assumed. A locked cell holds no `tabIndex` and so
      // takes no focus, which is what normally keeps the keys off it — but a
      // write is not something to let the tab order guarantee on its own.
      if (!held.current.isOpen(from)) return;
      event.preventDefault();
      writing.current(from, typed);
      return;
    }

    if (!isNavigationKey(event.key)) return;

    const to = nextCell(held.current, from, event.key);
    if (!to) return;

    // Taken only once there is somewhere to go: at the edge of the grid the
    // key is left alone, so Home still reaches the top of a long page.
    event.preventDefault();

    const landing = event.currentTarget.querySelector<HTMLElement>(
      `[data-cell="${cellId(to)}"]`,
    );
    landing?.focus();
    if (landing) reveal(landing);
  }, []);

  /**
   * Where the focus went, however it got there.
   *
   * Reading the focus rather than the keys is what makes a cell reached with
   * the mouse the one Tab comes back to.
   */
  const onFocus = useCallback((event: React.FocusEvent<HTMLElement>) => {
    const cell = parseCellId((event.target as HTMLElement).dataset?.cell);
    if (cell) setCursor(cell);
  }, []);

  const stop = tabStop(grid, cursor);

  return {
    onKeyDown,
    onFocus,
    /** Whether this cell is the grid's one stop in the tab order. */
    isTabStop: (cell: GridCell) =>
      stop !== null && stop.projectId === cell.projectId && stop.day === cell.day,
  };
}

/**
 * Brings a cell out from under the frozen column.
 *
 * The browser scrolls a focused cell into view on its own, but it counts the
 * viewport's left edge — and the mission column is pinned over it. A cell the
 * browser considers visible can therefore sit entirely behind the names. The
 * right-hand edge needs no such help: nothing is pinned there.
 */
function reveal(cell: HTMLElement): void {
  const scroller = cell.closest<HTMLElement>("[data-grid-scroller]");
  const frozen = cell.closest("tr")?.querySelector("th");
  if (!scroller || !frozen) return;

  const hidden =
    frozen.getBoundingClientRect().right - cell.getBoundingClientRect().left;
  if (hidden > 0) scroller.scrollLeft -= hidden;
}
