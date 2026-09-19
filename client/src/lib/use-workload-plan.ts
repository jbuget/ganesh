"use client";

import { arrayMove } from "@dnd-kit/sortable";
import { useCallback, useEffect, useState } from "react";

import { projectWorkload } from "@/lib/api/generated/planning/planning";
import type { WorkloadPlanResponse } from "@/lib/api/generated/model";
import { DEFAULT_HORIZON } from "@/lib/planning";

/** A what-if, as the screen holds it: a queue to serve, and who is on what. */
interface Scenario {
  horizonMonths: number;
  /** Missions to serve first. Empty means the order the team decided. */
  order: number[];
  /** Who to put on a mission. Absent means the team it actually has. */
  staffing: Record<number, number[]>;
}

const NO_SCENARIO: Scenario = {
  horizonMonths: DEFAULT_HORIZON,
  order: [],
  staffing: {},
};

/** Whether anything has been supposed, which is what the screen announces. */
function isHypothesis(scenario: Scenario): boolean {
  return scenario.order.length > 0 || Object.keys(scenario.staffing).length > 0;
}

/**
 * State of the planning screen: a scenario, and what it would cost.
 *
 * The scenario lives here and nowhere else. Moving a mission or putting
 * somebody on it changes what is asked of the server, never what the server
 * holds: one reads who lands later for it, and the board only moves if someone
 * decides to move it. Leaving the screen forgets the scenario, which is the
 * point — a hypothesis nobody acted on must not survive as a half-decision.
 */
export function useWorkloadPlanScreen() {
  const [scenario, setScenario] = useState<Scenario>(NO_SCENARIO);
  const [plan, setPlan] = useState<WorkloadPlanResponse | null>(null);
  //: The scenario the answer in hand was asked for. Comparing it to the one
  //: being edited is what says whether a projection is still on its way —
  //: raising a flag on the way into the effect would cost a render for
  //: nothing, and React says so out loud.
  const [answered, setAnswered] = useState<Scenario | null>(null);
  const [failed, setFailed] = useState<Scenario | null>(null);

  useEffect(() => {
    let alive = true;
    projectWorkload({
      horizon_months: scenario.horizonMonths,
      order: scenario.order,
      staffing: scenario.staffing,
    })
      .then((response) => {
        if (!alive) return;
        setPlan(response.data as WorkloadPlanResponse);
        setAnswered(scenario);
      })
      .catch(() => {
        if (alive) setFailed(scenario);
      });
    return () => {
      alive = false;
    };
  }, [scenario]);

  const isLoading = answered !== scenario && failed !== scenario;
  const hasError = failed === scenario;

  const missions = plan?.missions ?? [];
  // The order the server actually served, which is what a move rearranges.
  const served = missions.map((mission) => mission.project_id);

  const reorder = useCallback(
    (projectId: number, to: number) => {
      const from = served.indexOf(projectId);
      if (from === -1) return;

      const rank = Math.max(0, Math.min(to, served.length - 1));
      if (rank === from) return;

      setScenario((current) => ({ ...current, order: arrayMove(served, from, rank) }));
    },
    [served],
  );

  return {
    plan,
    missions,
    isLoading,
    hasError,
    horizonMonths: scenario.horizonMonths,
    isHypothesis: isHypothesis(scenario),

    setHorizon: (months: number) =>
      setScenario((current) => ({ ...current, horizonMonths: months })),

    /** Puts a mission at a new rank, and asks what it costs the others. */
    move: reorder,
    /** Sends a mission straight to the front — forty ranks in one click. */
    moveToTop: (projectId: number) => reorder(projectId, 0),
    moveUp: (projectId: number) => reorder(projectId, served.indexOf(projectId) - 1),
    moveDown: (projectId: number) => reorder(projectId, served.indexOf(projectId) + 1),

    /** Supposes a mission is carried by these people, and nobody else. */
    staff: (projectId: number, userIds: number[]) =>
      setScenario((current) => ({
        ...current,
        staffing: { ...current.staffing, [projectId]: userIds },
      })),

    /** Drops every hypothesis, keeping how far ahead one is looking. */
    reset: () =>
      setScenario((current) => ({
        ...NO_SCENARIO,
        horizonMonths: current.horizonMonths,
      })),
  };
}
