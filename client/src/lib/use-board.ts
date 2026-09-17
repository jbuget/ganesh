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
 */
export function useBoard() {
  const queryClient = useQueryClient();
  const { user } = useCurrentUser();
  const [colonnes, setColonnes] = useState<Colonnes | null>(null);
  const [enErreur, setEnErreur] = useState(false);

  useEffect(() => {
    let vivant = true;
    getBoard().then((reponse) => {
      if (vivant) setColonnes(versColonnes(reponse.data as BoardResponse));
    });
    return () => {
      vivant = false;
    };
  }, []);

  async function recharger() {
    const reponse = await getBoard();
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
