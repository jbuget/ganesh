"use client";

import { useMemo } from "react";

import {
  NO_USER_FILTER,
  hasActiveUserFilter,
  readUserFilters,
  writeUserFilters,
  type UserFilters,
} from "@/lib/user-filters";
import { writeUrl, useQueryString } from "@/lib/url-state";

/**
 * The filters of the team list, held by the URL.
 *
 * Every setting replaces the current step rather than adding one: one ticks two
 * roles in a row, and going back returns to the previous screen, not to the
 * second click.
 */
export function useUserFilters() {
  const query = useQueryString();
  const filters = useMemo(() => readUserFilters(new URLSearchParams(query)), [query]);

  function apply(next: UserFilters) {
    writeUrl((params) => writeUserFilters(params, next), "replace");
  }

  return {
    filters,
    hasFilter: hasActiveUserFilter(filters),

    /** Changes a single criterion, the others stay put. */
    set(change: Partial<UserFilters>) {
      apply({ ...filters, ...change });
    },

    clear() {
      apply(NO_USER_FILTER);
    },
  };
}
