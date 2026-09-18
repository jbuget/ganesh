"use client";

import { useCallback, useEffect, useState } from "react";

import type { ProjectUpdateResponse } from "@/lib/api/generated/model";
import {
  editProjectUpdate,
  listProjectUpdates,
  postProjectUpdate,
  removeProjectUpdate,
} from "@/lib/api/generated/projects/projects";

/**
 * A mission's follow-up thread.
 *
 * Every write is read back from the server: it decides the order, what stays
 * visible of a withdrawn update, and who is allowed to touch it.
 */
export function useProjectUpdates(
  projectId: number,
  /**
   * Called after every write: the thread is not read here alone. The reference
   * list and the kanban announce its count and its latest message, and would
   * otherwise sit on what they knew when the panel opened.
   */
  onWrite?: () => void | Promise<void>,
) {
  const [thread, setThread] = useState<ProjectUpdateResponse[] | null>(null);

  const reload = useCallback(async () => {
    const response = await listProjectUpdates(projectId);
    setThread(response.data as ProjectUpdateResponse[]);
  }, [projectId]);

  useEffect(() => {
    let alive = true;
    listProjectUpdates(projectId).then((response) => {
      if (alive) setThread(response.data as ProjectUpdateResponse[]);
    });
    return () => {
      alive = false;
    };
  }, [projectId]);

  return {
    thread,

    async publish(body: string) {
      await postProjectUpdate(projectId, { body });
      await reload();
      await onWrite?.();
    },

    async edit(updateId: number, body: string) {
      await editProjectUpdate(projectId, updateId, { body });
      await reload();
      await onWrite?.();
    },

    async remove(updateId: number) {
      await removeProjectUpdate(projectId, updateId);
      await reload();
      await onWrite?.();
    },
  };
}
