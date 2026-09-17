"use client";

import { useMemo } from "react";

import {
  writeSort,
  readSort,
  triSuivant,
  type SortColumn,
  type MissionSort,
} from "@/lib/mission-sort";
import { writeUrl, useQueryString } from "@/lib/url-state";

/**
 * L'ordre d'un ecran de missions, tenu par l'URL.
 *
 * Comme les filtres : un tableau range d'une certaine facon se partage par un
 * lien, et survit a un rechargement. Chaque clic remplace l'etape courante —
 * on cherche le bon ordre par essais successifs, et le retour arriere doit
 * ramener a l'ecran d'avant, pas au clic precedent.
 */
export function useMissionSort() {
  const query = useQueryString();
  const sorted = useMemo(() => readSort(new URLSearchParams(query)), [query]);

  return {
    sorted,

    /** Fait passer une colonne a l'etape suivante de son cycle. */
    toggle(column: SortColumn) {
      const suivant: MissionSort = triSuivant(sorted, column);
      writeUrl((params) => writeSort(params, suivant), "remplacer");
    },
  };
}
