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
 * Les filtres d'un ecran de missions, tenus par l'URL.
 *
 * Chaque reglage remplace l'etape courante plutot que d'en ajouter une : on
 * coche trois phases a la suite, et le retour arriere ramene a l'ecran d'avant,
 * pas au troisieme clic.
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

    /** Change un seul critere, les autres restent en place. */
    set(change: Partial<MissionFilters>) {
      apply({ ...filters, ...change });
    },

    clear() {
      apply(NO_FILTER);
    },
  };
}
