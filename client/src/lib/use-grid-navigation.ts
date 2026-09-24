"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  cellId,
  isNavigationKey,
  nextCell,
  parseCellId,
  tabStop,
  type GridCell,
  type NavigableGrid,
} from "@/lib/grid-navigation";

/**
 * The keys wired to the entry grid.
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
export function useGridNavigation(grid: NavigableGrid) {
  // Where the hand last was, which is where Tab comes back to.
  const [cursor, setCursor] = useState<GridCell | null>(null);

  const held = useRef(grid);
  useEffect(() => {
    held.current = grid;
  });

  const onKeyDown = useCallback((event: React.KeyboardEvent<HTMLElement>) => {
    if (!isNavigationKey(event.key)) return;

    const from = parseCellId((event.target as HTMLElement).dataset?.cell);
    if (!from) return;

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
