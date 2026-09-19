"use client";

import { useMemo } from "react";

import {
  nextUserSort,
  readUserSort,
  writeUserSort,
  type UserSort,
  type UserSortColumn,
} from "@/lib/user-sort";
import { writeUrl, useQueryString } from "@/lib/url-state";

/**
 * The order of the team list, held by the URL.
 *
 * Like the mission reference list: a list arranged a certain way is shared by a
 * link, and survives a reload. Every click replaces the current step — one
 * looks for the right order by trying, and going back must return to the
 * previous screen, not to the previous click.
 */
export function useUserSort() {
  const query = useQueryString();
  const sorted = useMemo(() => readUserSort(new URLSearchParams(query)), [query]);

  return {
    sorted,

    /** Moves a column to the next step of its cycle. */
    toggle(column: UserSortColumn) {
      const next: UserSort = nextUserSort(sorted, column);
      writeUrl((params) => writeUserSort(params, next), "replace");
    },
  };
}
