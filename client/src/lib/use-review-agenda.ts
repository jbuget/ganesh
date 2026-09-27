"use client";

import { useCallback, useEffect, useState } from "react";

import type { FlaggedUpdateResponse } from "@/lib/api/generated/model";
import {
  clearProjectUpdateFlag,
  listFlaggedUpdates,
} from "@/lib/api/generated/projects/projects";
import { type AgendaChapter, countWaiting, groupByProject } from "@/lib/review-agenda";

/**
 * What the next revue has to discuss.
 *
 * Read back from the server after every write: it decides the order, and
 * lowering a mark is a gesture of the meeting — two people clearing the same
 * line must not end up on two different agendas.
 */
export function useReviewAgenda() {
  const [chapters, setChapters] = useState<AgendaChapter[] | null>(null);

  const reload = useCallback(async () => {
    const response = await listFlaggedUpdates();
    setChapters(groupByProject(response.data as FlaggedUpdateResponse[]));
  }, []);

  useEffect(() => {
    let alive = true;
    listFlaggedUpdates().then((response) => {
      if (alive) setChapters(groupByProject(response.data as FlaggedUpdateResponse[]));
    });
    return () => {
      alive = false;
    };
  }, []);

  return {
    chapters,

    /** How many lines are waiting, across every project. */
    waiting: chapters === null ? 0 : countWaiting(chapters),

    /** Takes a line off the agenda, the revue having read it. */
    async clear(projectId: number, updateId: number) {
      await clearProjectUpdateFlag(projectId, updateId);
      await reload();
    },
  };
}
