"use client";

import { useMemo } from "react";

import {
  EVERY_REQUEST,
  hasActiveRequestFilter,
  readRequestFilters,
  writeRequestFilters,
  type RequestFilters,
} from "@/lib/request-filters";
import { writeUrl, useQueryString } from "@/lib/url-state";

/**
 * The criteria of the list of needs, held by the URL.
 *
 * Every setting replaces the current step rather than adding one: one ticks
 * two states in a row, and going back returns to the previous screen, not to
 * the second click.
 */
export function useRequestFilters() {
  const query = useQueryString();
  const filters = useMemo(
    () => readRequestFilters(new URLSearchParams(query)),
    [query],
  );

  function apply(next: RequestFilters) {
    writeUrl((params) => writeRequestFilters(params, next), "replace");
  }

  return {
    filters,
    hasFilter: hasActiveRequestFilter(filters),

    /** Changes a single criterion, the others stay put. */
    set(change: Partial<RequestFilters>) {
      apply({ ...filters, ...change });
    },

    /** Everything, in every state: « Effacer » takes the default off too. */
    clear() {
      apply(EVERY_REQUEST);
    },
  };
}
