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
export type Columns = Record<ProjectStatus, BoardCardResponse[]>;

/** Archived ones are only asked for when they are wanted. */
function scope(includeArchived: boolean) {
  return includeArchived ? { include_inactive: true } : undefined;
}

function toColumns(board: BoardResponse): Columns {
  return Object.fromEntries(
    board.columns.map((column) => [column.status, column.cards]),
  ) as Columns;
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
export function useBoard(includeArchived = false) {
  const queryClient = useQueryClient();
  const { user } = useCurrentUser();
  const [columns, setColumns] = useState<Columns | null>(null);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let alive = true;
    getBoard(scope(includeArchived)).then((response) => {
      if (alive) setColumns(toColumns(response.data as BoardResponse));
    });
    return () => {
      alive = false;
    };
  }, [includeArchived]);

  async function reload() {
    const response = await getBoard(scope(includeArchived));
    setColumns(toColumns(response.data as BoardResponse));
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
    preview: setColumns,

    /** Takes the server's truth back, after a change made outside a drag. */
    reload,

    /** Applies the move on screen, then saves it. */
    async move(
      projectId: number,
      toStatus: ProjectStatus,
      toPosition: number,
      nextColumns: Columns,
    ) {
      setColumns(nextColumns);
      setHasError(false);
      try {
        await moveProject(projectId, {
          status: toStatus,
          position: toPosition,
        });
        await queryClient.invalidateQueries();
      } catch {
        // The screen must never sit on a state the server knows nothing of.
        setHasError(true);
        await reload();
      }
    },
  };
}
