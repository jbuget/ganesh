"use client";

import { useMemo } from "react";

import {
  EVERY_CRITERION,
  NO_FILTER,
  writeFilters,
  hasActiveFilter,
  readFilters,
  type Criterion,
  type MissionFilters,
} from "@/lib/mission-filters";
import { writeUrl, useQueryString } from "@/lib/url-state";

/**
 * The filters of a mission screen, held by the URL.
 *
 * Every setting replaces the current step rather than adding one: one ticks
 * three phases in a row, and going back returns to the previous screen, not to
 * the third click.
 *
 * `criteria` says which questions the screen asks; the others are neither
 * read from the address nor counted as active. A screen that does not offer
 * a criterion cannot show it, and must therefore not answer for it. Pass a
 * constant declared outside the component: the filters are read against it,
 * and a list rebuilt on every render would hand back a new object each time,
 * which anything watching them would read as a change.
 */
export function useMissionFilters(criteria: Criterion[] = EVERY_CRITERION) {
  const query = useQueryString();
  const filters = useMemo(
    () => readFilters(new URLSearchParams(query), criteria),
    [query, criteria],
  );

  function apply(next: MissionFilters) {
    writeUrl((params) => writeFilters(params, next), "replace");
  }

  return {
    filters,
    hasFilter: hasActiveFilter(filters, criteria),

    /** Changes a single criterion, the others stay put. */
    set(change: Partial<MissionFilters>) {
      apply({ ...filters, ...change });
    },

    clear() {
      apply(NO_FILTER);
    },
  };
}
