"use client";

import { useMemo } from "react";

import {
  NO_FILTER,
  writeFilters,
  hasActiveFilter,
  readFilters,
  type MissionFilters,
} from "@/lib/mission-filters";
import { writeUrl, useQueryString } from "@/lib/url-state";

/**
 * The filters of a mission screen, held by the URL.
 *
 * Every setting replaces the current step rather than adding one: one ticks
 * three phases in a row, and going back returns to the previous screen, not to
 * the third click.
 */
export function useMissionFilters() {
  const query = useQueryString();
  const filters = useMemo(() => readFilters(new URLSearchParams(query)), [query]);

  function apply(next_ones: MissionFilters) {
    writeUrl((params) => writeFilters(params, next_ones), "remplacer");
  }

  return {
    filters,
    hasFilter: hasActiveFilter(filters),

    /** Changes a single criterion, the others stay put. */
    set(change: Partial<MissionFilters>) {
      apply({ ...filters, ...change });
    },

    clear() {
      apply(NO_FILTER);
    },
  };
}
