"use client";

import { useMemo } from "react";

import {
  NO_FILTER,
  ecrireFiltres,
  filtreActif,
  lireFiltres,
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
  const filters = useMemo(() => lireFiltres(new URLSearchParams(query)), [query]);

  function apply(next_ones: MissionFilters) {
    writeUrl((params) => ecrireFiltres(params, next_ones), "remplacer");
  }

  return {
    filters,
    hasFilter: filtreActif(filters),

    /** Changes a single criterion, the others stay put. */
    set(change: Partial<MissionFilters>) {
      apply({ ...filters, ...change });
    },

    clear() {
      apply(NO_FILTER);
    },
  };
}
