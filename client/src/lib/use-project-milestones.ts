"use client";

import { useCallback, useEffect, useState } from "react";

import type { MilestoneResponse } from "@/lib/api/generated/model";
import {
  createProjectMilestone,
  deleteProjectMilestone,
  listProjectMilestones,
  updateProjectMilestone,
} from "@/lib/api/generated/projects/projects";

/**
 * The dates a mission answers for, and the gestures that change them.
 *
 * Every change is saved then read back from the server, as the rest of the
 * sheet is: the list is edited field by field, with no « Enregistrer », and
 * the screen must never show anything the database does not hold. Reading
 * back is also what keeps the order right — the server sorts them by the day
 * they happen, and a date moved changes where its line belongs.
 */
export function useProjectMilestones(projectId: number) {
  const [milestones, setMilestones] = useState<MilestoneResponse[]>([]);
  const [isLoading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    const answer = await listProjectMilestones(projectId);
    setMilestones(answer.status === 200 ? answer.data : []);
    setLoading(false);
  }, [projectId]);

  useEffect(() => {
    let abandoned = false;
    // Detached rather than awaited in the effect body: setting state as the
    // effect runs cascades a render, and a panel closed meanwhile must not
    // be written into.
    void (async () => {
      const answer = await listProjectMilestones(projectId);
      if (abandoned) return;
      setMilestones(answer.status === 200 ? answer.data : []);
      setLoading(false);
    })();
    return () => {
      abandoned = true;
    };
  }, [projectId]);

  return {
    milestones,
    isLoading,

    async add(label: string, expectedOn: string) {
      await createProjectMilestone(projectId, {
        label,
        expected_on: expectedOn,
      });
      await reload();
    },

    /**
     * Changes one field of a milestone.
     *
     * Only what is named travels: leaving a field out is how one says « leave
     * it as it is », which is what lets a milestone be marked reached without
     * touching the day it was announced for. Naming `reached_on` as null is
     * how one crossed by mistake is put back.
     */
    async change(
      milestoneId: number,
      fields: { label?: string; expected_on?: string; reached_on?: string | null },
    ) {
      await updateProjectMilestone(projectId, milestoneId, fields);
      await reload();
    },

    async remove(milestoneId: number) {
      await deleteProjectMilestone(projectId, milestoneId);
      await reload();
    },
  };
}
