"use client";

import { useCallback, useEffect, useState } from "react";

import type { ActivityResponse, WorkNature } from "@/lib/api/generated/model";
import {
  archiveProjectActivity,
  createProjectActivity,
  listProjectActivities,
  unarchiveProjectActivity,
  updateProjectActivity,
} from "@/lib/api/generated/projects/projects";

/**
 * The trades a mission is cut into, and the gestures that change them.
 *
 * Every change is saved then read back from the server, as the rest of the
 * sheet is: the list is edited field by field, with no « Enregistrer », and
 * the screen must never show anything the database does not hold.
 */
export function useProjectActivities(
  projectId: number,
  /** Called after every write: the estimate of the mission follows from these. */
  onWrite?: () => void | Promise<void>,
) {
  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [isLoading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    const answer = await listProjectActivities(projectId);
    setActivities(answer.status === 200 ? answer.data : []);
    setLoading(false);
  }, [projectId]);

  useEffect(() => {
    let abandoned = false;
    // Detached rather than awaited in the effect body: setting state as the
    // effect runs cascades a render, and a panel closed meanwhile must not
    // be written into.
    void (async () => {
      const answer = await listProjectActivities(projectId);
      if (abandoned) return;
      setActivities(answer.status === 200 ? answer.data : []);
      setLoading(false);
    })();
    return () => {
      abandoned = true;
    };
  }, [projectId]);

  const afterWrite = useCallback(async () => {
    await reload();
    await onWrite?.();
  }, [reload, onWrite]);

  return {
    activities,
    isLoading,

    async add(label: string, nature: WorkNature | null) {
      await createProjectActivity(projectId, {
        label,
        nature,
        estimated_days: null,
      });
      await afterWrite();
    },

    /**
     * Changes one field of an activity.
     *
     * Only what is named travels: leaving a field out is how one says « leave
     * it as it is », which is what lets the estimate be edited without
     * blanking the trade beside it.
     */
    async change(
      activityId: number,
      fields: {
        label?: string;
        nature?: WorkNature | null;
        estimated_days?: number | null;
      },
    ) {
      await updateProjectActivity(projectId, activityId, fields);
      await afterWrite();
    },

    async archive(activityId: number) {
      await archiveProjectActivity(projectId, activityId);
      await afterWrite();
    },

    async unarchive(activityId: number) {
      await unarchiveProjectActivity(projectId, activityId);
      await afterWrite();
    },
  };
}
