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

/** Columns indexed by phase, a handy shape for drag and drop. */
export type Colonnes = Record<ProjectStatus, BoardCardResponse[]>;

/** Archived ones are only asked for when they are wanted. */
function scope(inclureArchivees: boolean) {
  return inclureArchivees ? { include_inactive: true } : undefined;
}

function versColonnes(board: BoardResponse): Colonnes {
  return Object.fromEntries(
    board.columns.map((column) => [column.status, column.cards]),
  ) as Colonnes;
}

/**
 * Board state and card moves.
 *
 * Columns are held locally: a drag and drop must show at once, without waiting
 * for the server round trip. The call follows, and a failure reloads the
 * server's truth rather than leaving a screen that lies.
 *
 * Archived missions only travel on request: the board is there to steer what is
 * running, and loading them on every opening would make everyone pay for what
 * is rarely used.
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
     * Shows a state without saving it.
     *
     * That is what happens during a drag: columns open and close under the
     * cursor, but nothing is written until the card is released.
     */
    preview: setColonnes,

    /** Takes the server's truth back, after a change made outside a drag. */
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
        // The screen must never sit on a state the server knows nothing of.
        setEnErreur(true);
        await reload();
      }
    },
  };
}
