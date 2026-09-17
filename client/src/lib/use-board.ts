"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getBoard, moveProject } from "@/lib/api/generated/projects/projects";
import type {
  BoardCardResponse,
  BoardResponse,
  ProjectStatus,
} from "@/lib/api/generated/model";
import { useCurrentUser } from "@/lib/api/queries";
import { useEffect } from "react";

/** Colonnes indexees par phase, forme pratique pour le glisser-deposer. */
export type Colonnes = Record<ProjectStatus, BoardCardResponse[]>;

/** Les archivees ne sont demandees que lorsqu'on veut les voir. */
function perimetre(inclureArchivees: boolean) {
  return inclureArchivees ? { include_inactive: true } : undefined;
}

function versColonnes(board: BoardResponse): Colonnes {
  return Object.fromEntries(
    board.colonnes.map((colonne) => [colonne.statut, colonne.cartes]),
  ) as Colonnes;
}

/**
 * Etat du tableau de bord et deplacement des cartes.
 *
 * Les colonnes sont tenues localement : un glisser-deposer doit se voir
 * immediatement, sans attendre l'aller-retour serveur. L'appel suit, et un
 * echec recharge la verite du serveur plutot que de laisser un ecran qui ment.
 *
 * Les missions archivees ne voyagent que sur demande : le tableau sert a
 * piloter ce qui tourne, et les charger a chaque ouverture ferait payer a tous
 * ce dont on se sert rarement.
 */
export function useBoard(inclureArchivees = false) {
  const queryClient = useQueryClient();
  const { user } = useCurrentUser();
  const [colonnes, setColonnes] = useState<Colonnes | null>(null);
  const [enErreur, setEnErreur] = useState(false);

  useEffect(() => {
    let vivant = true;
    getBoard(perimetre(inclureArchivees)).then((reponse) => {
      if (vivant) setColonnes(versColonnes(reponse.data as BoardResponse));
    });
    return () => {
      vivant = false;
    };
  }, [inclureArchivees]);

  async function recharger() {
    const reponse = await getBoard(perimetre(inclureArchivees));
    setColonnes(versColonnes(reponse.data as BoardResponse));
    await queryClient.invalidateQueries();
  }

  return {
    colonnes,
    enErreur,
    utilisateur: user,

    /**
     * Montre un etat sans l'enregistrer.
     *
     * C'est ce qui se joue pendant un glissement : les colonnes s'ouvrent et se
     * referment sous le curseur, mais rien n'est ecrit tant que la carte n'est
     * pas relachee.
     */
    previsualiser: setColonnes,

    /** Reprend la verite du serveur, apres un changement fait hors glissement. */
    recharger,

    /** Applique le deplacement a l'ecran, puis l'enregistre. */
    async deplacer(
      projectId: number,
      versStatut: ProjectStatus,
      versPosition: number,
      colonnesApres: Colonnes,
    ) {
      setColonnes(colonnesApres);
      setEnErreur(false);
      try {
        await moveProject(projectId, {
          statut: versStatut,
          position: versPosition,
        });
        await queryClient.invalidateQueries();
      } catch {
        // L'ecran ne doit jamais rester sur un etat que le serveur ignore.
        setEnErreur(true);
        await recharger();
      }
    },
  };
}
