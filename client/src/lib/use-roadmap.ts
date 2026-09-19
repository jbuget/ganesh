"use client";

import { useCallback, useEffect, useState } from "react";

import { readRoadmap } from "@/lib/api/generated/planning/planning";
import { updateProject } from "@/lib/api/generated/projects/projects";
import type { RoadmapResponse } from "@/lib/api/generated/model";
import { civilYearOf, type Grouping } from "@/lib/roadmap";

/**
 * State of the roadmap screen: a window, a grouping, and the drawing.
 *
 * The window is the only thing that costs a request. The grouping regroups
 * what is already in hand — a committee flips from axes to phases while
 * talking, and waiting on the server each time would break the conversation.
 */
export function useRoadmapScreen() {
  const [year, setYear] = useState<number>(() => new Date().getFullYear());
  const [grouping, setGrouping] = useState<Grouping>("category");
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  //: The year the drawing in hand was asked for. Comparing it to the one
  //: being read is what says whether an answer is still on its way, without
  //: a flag to keep in step with the request.
  const [answered, setAnswered] = useState<number | null>(null);
  const [failed, setFailed] = useState<number | null>(null);

  const fetchYear = useCallback(
    (asked: number, isStillWanted: () => boolean = () => true) => {
      const [from, to] = civilYearOf(asked);
      return readRoadmap({ from_day: from, to_day: to })
        .then((response) => {
          if (!isStillWanted()) return;
          setRoadmap(response.data as RoadmapResponse);
          setAnswered(asked);
          setFailed(null);
        })
        .catch(() => {
          if (isStillWanted()) setFailed(asked);
        });
    },
    [],
  );

  useEffect(() => {
    let alive = true;
    void fetchYear(year, () => alive);
    return () => {
      alive = false;
    };
  }, [year, fetchYear]);

  return {
    roadmap,
    isLoading: answered !== year && failed !== year,
    hasError: failed === year,
    year,
    setYear,
    grouping,
    setGrouping,

    /**
     * Posts the date a mission is announced for.
     *
     * The whole drawing is read again afterwards rather than the one line
     * patched: moving a date moves nothing else, but the tally above it does,
     * and a screen whose bars and tally disagree is worse than one that waits
     * a moment.
     */
    async setTargetDate(projectId: number, target: string | null) {
      await updateProject(projectId, { go_live_date: target });
      await fetchYear(year);
    },
  };
}
