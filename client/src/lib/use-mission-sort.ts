"use client";

import { useMemo } from "react";

import {
  ecrireTri,
  lireTri,
  triSuivant,
  type ColonneTri,
  type TriMissions,
} from "@/lib/mission-sort";
import { ecrireUrl, useQueryString } from "@/lib/url-state";

/**
 * L'ordre d'un ecran de missions, tenu par l'URL.
 *
 * Comme les filtres : un tableau range d'une certaine facon se partage par un
 * lien, et survit a un rechargement. Chaque clic remplace l'etape courante —
 * on cherche le bon ordre par essais successifs, et le retour arriere doit
 * ramener a l'ecran d'avant, pas au clic precedent.
 */
export function useMissionSort() {
  const requete = useQueryString();
  const tri = useMemo(() => lireTri(new URLSearchParams(requete)), [requete]);

  return {
    tri,

    /** Fait passer une colonne a l'etape suivante de son cycle. */
    basculer(colonne: ColonneTri) {
      const suivant: TriMissions = triSuivant(tri, colonne);
      ecrireUrl((params) => ecrireTri(params, suivant), "remplacer");
    },
  };
}
