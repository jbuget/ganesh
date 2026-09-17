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
function scope(inclureArchivees: boolean) {
  return inclureArchivees ? { include_inactive: true } : undefined;
}

function versColonnes(board: BoardResponse): Colonnes {
  return Object.fromEntries(
    board.columns.map((column) => [column.status, column.cards]),
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
  const [columns, setColonnes] = useState<Colonnes | null>(null);
  const [hasError, setEnErreur] = useState(false);

  useEffect(() => {
    let alive = true;
    getBoard(scope(inclureArchivees)).then((response) => {
      if (alive) setColonnes(versColonnes(response.data as BoardResponse));
    });
    return () => {
      alive = false;
    };
  }, [inclureArchivees]);

  async function reload() {
    const response = await getBoard(scope(inclureArchivees));
    setColonnes(versColonnes(response.data as BoardResponse));
    await queryClient.invalidateQueries();
  }

  return {
    columns,
    hasError,
    user: user,

    /**
     * Montre un etat sans l'enregistrer.
     *
     * C'est ce qui se joue pendant un glissement : les colonnes s'ouvrent et se
     * referment sous le curseur, mais rien n'est ecrit tant que la carte n'est
     * pas relachee.
     */
    preview: setColonnes,

    /** Reprend la verite du serveur, apres un changement fait hors glissement. */
    reload,

    /** Applique le deplacement a l'ecran, puis l'enregistre. */
    async move(
      projectId: number,
      versStatut: ProjectStatus,
      versPosition: number,
      colonnesApres: Colonnes,
    ) {
      setColonnes(colonnesApres);
      setEnErreur(false);
      try {
        await moveProject(projectId, {
          status: versStatut,
          position: versPosition,
        });
        await queryClient.invalidateQueries();
      } catch {
        // L'ecran ne doit jamais rester sur un etat que le serveur ignore.
        setEnErreur(true);
        await reload();
      }
    },
  };
}
