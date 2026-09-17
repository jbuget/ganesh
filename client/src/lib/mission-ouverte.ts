"use client";

import { ecrireUrl, useQueryString } from "@/lib/url-state";

const PARAMETRE = "mission";
const ONGLET = "onglet";

/**
 * La mission ouverte dans le panneau lateral, tenue par l'URL.
 *
 * L'URL est la source : un panneau se partage par un lien, et le retour arriere
 * le referme. L'ouverture pousse donc une etape d'historique, et ne touche
 * qu'a ses parametres : les filtres du tableau doivent survivre a l'aller-retour
 * dans un panneau.
 *
 * L'onglet en fait partie : on ouvre une mission sur sa fiche, mais on l'ouvre
 * sur son fil quand c'est le fil qu'on est alle chercher.
 */
export function useMissionOuverte() {
  const requete = useQueryString();
  const params = new URLSearchParams(requete);
  const valeur = params.get(PARAMETRE);

  return {
    missionOuverte: Number(valeur) || null,
    ongletOuvert: params.get(ONGLET),

    ouvrir(projectId: number, onglet?: string) {
      ecrireUrl((params) => {
        params.set(PARAMETRE, String(projectId));
        // Sans effacement, l'onglet d'une ouverture precedente s'appliquerait
        // a la mission suivante.
        if (onglet) params.set(ONGLET, onglet);
        else params.delete(ONGLET);
      });
    },

    fermer() {
      ecrireUrl((params) => {
        params.delete(PARAMETRE);
        params.delete(ONGLET);
      });
    },
  };
}
