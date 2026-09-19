"use client";

import { useMemo } from "react";

import {
  NO_HIDDEN_COLUMN,
  isHideable,
  readHiddenColumns,
  tableWidth,
  writeHiddenColumns,
  type ColumnKey,
  type HiddenColumns,
} from "@/lib/mission-columns";
import { NO_SORT, writeSort, type MissionSort } from "@/lib/mission-sort";
import { writeUrl, useQueryString } from "@/lib/url-state";

/**
 * The columns a mission screen shows, held by the URL.
 *
 * Like the filters and the order: a reference list read a certain way is shared
 * by a link — « voilà l'écran du point de pilotage » — and survives a reload.
 * Each choice replaces the current step rather than adding one: one puts three
 * columns away in a row, and going back must return to the previous screen.
 *
 * It is told the order so it can release it: put away the column a list is
 * sorted by, and the rows keep an arrangement nothing on screen accounts for.
 * Both are written in one go, so the address never passes through a state where
 * the list is ordered by a column it no longer shows.
 */
export function useMissionColumns(sorted: MissionSort) {
  const query = useQueryString();
  const hidden = useMemo(() => readHiddenColumns(new URLSearchParams(query)), [query]);

  function apply(next: HiddenColumns) {
    writeUrl((params) => {
      writeHiddenColumns(params, next);

      const ordered = sorted.column;
      if (ordered && isHideable(ordered) && next.has(ordered)) {
        writeSort(params, NO_SORT);
      }
    }, "replace");
  }

  return {
    hidden,
    isVisible: (column: ColumnKey) => !hidden.has(column),

    /** How wide the table stands once the columns put away are gone. */
    width: tableWidth(hidden),

    /** Puts a column away, or brings it back. */
    toggle(column: ColumnKey) {
      const next = new Set(hidden);
      if (next.has(column)) next.delete(column);
      else next.add(column);
      apply(next);
    },

    /** The whole panorama back, without undoing each choice. */
    showAll() {
      apply(NO_HIDDEN_COLUMN);
    },
  };
}
