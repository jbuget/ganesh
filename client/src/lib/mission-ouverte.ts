"use client";

import { ecrireUrl, useQueryString } from "@/lib/url-state";

const PARAMETRE = "mission";

/**
 * La mission ouverte dans le panneau lateral, tenue par l'URL.
 *
 * L'URL est la source : un panneau se partage par un lien, et le retour arriere
 * le referme. L'ouverture pousse donc une etape d'historique, et ne touche
 * qu'a son parametre : les filtres du tableau doivent survivre a l'aller-retour
 * dans un panneau.
 */
export function useMissionOuverte() {
  const requete = useQueryString();
  const valeur = new URLSearchParams(requete).get(PARAMETRE);

  return {
    missionOuverte: Number(valeur) || null,

    ouvrir(projectId: number) {
      ecrireUrl((params) => params.set(PARAMETRE, String(projectId)));
    },

    fermer() {
      ecrireUrl((params) => params.delete(PARAMETRE));
    },
  };
}
