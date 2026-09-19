"use client";

import { useCallback, useEffect, useState } from "react";

import { readRoadmap } from "@/lib/api/generated/planning/planning";
import { updateProject } from "@/lib/api/generated/projects/projects";
import type { RoadmapResponse } from "@/lib/api/generated/model";
import { DEFAULT_SPAN, type Grouping } from "@/lib/roadmap";

/**
 * State of the roadmap screen: a window, a grouping, and the drawing.
 *
 * The window is the only thing that costs a request. The grouping regroups
 * what is already in hand — a committee flips from axes to phases while
 * talking, and waiting on the server each time would break the conversation.
 */
export function useRoadmapScreen() {
  const [months, setMonths] = useState(DEFAULT_SPAN);
  const [grouping, setGrouping] = useState<Grouping>("category");
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  //: The span the drawing in hand was asked for. Comparing it to the one
  //: being read is what says whether an answer is still on its way, without
  //: a flag to keep in step with the request.
  const [answered, setAnswered] = useState<number | null>(null);
  const [failed, setFailed] = useState<number | null>(null);
  //: Whether the last date posted was refused. Held apart from a read that
  //: failed: one leaves the screen empty, the other leaves it right and the
  //: write lost, and saying « erreur » for both would tell the reader nothing.
  const [saveFailed, setSaveFailed] = useState(false);

  const fetchSpan = useCallback(
    (asked: number, isStillWanted: () => boolean = () => true) => {
      // The window itself is worked out by the server: where it opens and
      // how it lands on month boundaries is a rule, and a rule lives in one
      // place or it drifts.
      return readRoadmap({ months: asked })
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
    void fetchSpan(months, () => alive);
    return () => {
      alive = false;
    };
  }, [months, fetchSpan]);

  return {
    roadmap,
    isLoading: answered !== months && failed !== months,
    hasError: failed === months,
    months,
    setMonths,
    grouping,
    setGrouping,
    saveFailed,

    /** Reads the drawing again, after something changed it from elsewhere. */
    async refresh() {
      await fetchSpan(months);
    },

    /**
     * Posts the date a mission is announced for.
     *
     * The whole drawing is read again afterwards rather than the one line
     * patched: moving a date moves nothing else, but the tally above it does,
     * and a screen whose bars and tally disagree is worse than one that waits
     * a moment.
     *
     * A refusal is caught and said out loud. Letting it through would leave
     * the row showing a date the server never took, which is the one thing a
     * screen about commitments must not do.
     */
    async setTargetDate(projectId: number, target: string | null) {
      try {
        await updateProject(projectId, { go_live_date: target });
        setSaveFailed(false);
      } catch {
        setSaveFailed(true);
      }
      await fetchSpan(months);
    },
  };
}
