"use client";

import { arrayMove } from "@dnd-kit/sortable";
import { useState } from "react";

import { useWorkloadPlan as useWorkloadPlanQuery } from "@/lib/api/queries";
import { DEFAULT_HORIZON } from "@/lib/planning";

/**
 * State of the planning screen: an horizon, and a hypothesis on the order.
 *
 * The hypothesis lives here and nowhere else. Moving a mission changes what is
 * asked of the server, never what the server holds: one reads who lands later
 * for it, and the board only moves if someone decides to move it. Leaving the
 * screen forgets the hypothesis, which is the point — a scenario one did not
 * act on must not survive as a half-decision.
 */
export function useWorkloadPlanScreen() {
  const [horizonMonths, setHorizon] = useState<number>(DEFAULT_HORIZON);
  const [order, setOrder] = useState<number[]>([]);
  const { plan, isLoading, isError } = useWorkloadPlanQuery(horizonMonths, order);

  const missions = plan?.missions ?? [];

  /** Puts a mission at a new rank, and asks what it costs the others. */
  function move(projectId: number, to: number) {
    const ids = missions.map((mission) => mission.project_id);
    const from = ids.indexOf(projectId);
    if (from === -1) return;

    const rank = Math.max(0, Math.min(to, ids.length - 1));
    if (rank === from) return;

    setOrder(arrayMove(ids, from, rank));
  }

  return {
    plan,
    missions,
    isLoading,
    isError,
    horizonMonths,
    setHorizon,
    move,
    /** Whether what is shown is a hypothesis rather than the team's order. */
    isHypothesis: order.length > 0,
    reset: () => setOrder([]),
  };
}
