"use client";

import { useMemo } from "react";

import {
  AUCUN_FILTRE,
  ecrireFiltres,
  filtreActif,
  lireFiltres,
  type MissionFilters,
} from "@/lib/mission-filters";
import { ecrireUrl, useQueryString } from "@/lib/url-state";

/**
 * Les filtres d'un ecran de missions, tenus par l'URL.
 *
 * Chaque reglage remplace l'etape courante plutot que d'en ajouter une : on
 * coche trois phases a la suite, et le retour arriere ramene a l'ecran d'avant,
 * pas au troisieme clic.
 */
export function useMissionFilters() {
  const requete = useQueryString();
  const filtres = useMemo(() => lireFiltres(new URLSearchParams(requete)), [requete]);

  function poser(suivants: MissionFilters) {
    ecrireUrl((params) => ecrireFiltres(params, suivants), "remplacer");
  }

  return {
    filtres,
    actif: filtreActif(filtres),

    /** Change un seul critere, les autres restent en place. */
    definir(changement: Partial<MissionFilters>) {
      poser({ ...filtres, ...changement });
    },

    effacer() {
      poser(AUCUN_FILTRE);
    },
  };
}
