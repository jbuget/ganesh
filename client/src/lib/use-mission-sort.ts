"use client";

import { useMemo } from "react";

import {
  writeSort,
  readSort,
  nextSort,
  type SortColumn,
  type MissionSort,
} from "@/lib/mission-sort";
import { writeUrl, useQueryString } from "@/lib/url-state";

/**
 * The order of a mission screen, held by the URL.
 *
 * Like the filters: a list arranged a certain way is shared by a link, and
 * survives a reload. Every click replaces the current step — one looks for the
 * right order by trying, and going back must return to the previous screen, not
 * to the previous click.
 */
export function useMissionSort() {
  const query = useQueryString();
  const sorted = useMemo(() => readSort(new URLSearchParams(query)), [query]);

  return {
    sorted,

    /** Moves a column to the next step of its cycle. */
    toggle(column: SortColumn) {
      const next: MissionSort = nextSort(sorted, column);
      writeUrl((params) => writeSort(params, next), "replace");
    },
  };
}
