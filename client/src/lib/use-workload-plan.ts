"use client";

import { arrayMove } from "@dnd-kit/sortable";
import { useCallback, useEffect, useState } from "react";

import { projectWorkload } from "@/lib/api/generated/planning/planning";
import type {
  SimulationResponse,
  WorkloadPlanResponse,
} from "@/lib/api/generated/model";
import {
  DEFAULT_HORIZON,
  sameScenario,
  supposesSomething,
  type Scenario,
} from "@/lib/planning";
import { scenarioOf, useSimulations } from "@/lib/use-simulations";

const NO_SCENARIO: Scenario = {
  horizonMonths: DEFAULT_HORIZON,
  order: [],
  staffing: {},
};

/**
 * State of the planning screen: a scenario, and what it would cost.
 *
 * The scenario is edited here and projected by the server, which writes
 * nothing: moving a mission or putting somebody on it asks what that would
 * cost, it does not decide it. Saving is the one deliberate act that makes a
 * hypothesis survive the session — and even then it saves the question, never
 * the answer.
 */
export function useWorkloadPlanScreen() {
  const [scenario, setScenario] = useState<Scenario>(NO_SCENARIO);
  //: Which saved simulation is open, if any. A scenario edited afterwards
  //: stays attached to it until someone saves or picks another.
  const [openedId, setOpenedId] = useState<number | null>(null);
  const [plan, setPlan] = useState<WorkloadPlanResponse | null>(null);
  //: The scenario the answer in hand was asked for. Comparing it to the one
  //: being edited is what says whether a projection is still on its way.
  const [answered, setAnswered] = useState<Scenario | null>(null);
  const [failed, setFailed] = useState<Scenario | null>(null);

  const shelf = useSimulations();

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

  const missions = plan?.missions ?? [];
  // The order the server actually served, which is what a move rearranges.
  const served = missions.map((mission) => mission.project_id);

  const opened = shelf.simulations.find((s) => s.id === openedId) ?? null;

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

  /** Loads a saved scenario, or comes back to the order the team decided. */
  function open(simulation: SimulationResponse | null) {
    setScenario(simulation ? scenarioOf(simulation) : NO_SCENARIO);
    setOpenedId(simulation?.id ?? null);
    shelf.clearError();
  }

  async function saveAs(name: string) {
    const saved = await shelf.save(name, scenario);
    if (saved) setOpenedId(saved.id);
    return saved !== null;
  }

  async function saveOver() {
    if (!opened) return;
    await shelf.rewrite(opened, scenario);
  }

  async function remove(simulationId: number) {
    await shelf.remove(simulationId);
    // Dropping the scenario one was reading leaves the plan on it rather than
    // snapping back: what is on screen is still a legitimate question, it is
    // simply no longer written down anywhere.
    if (simulationId === openedId) setOpenedId(null);
  }

  return {
    plan,
    missions,
    isLoading: answered !== scenario && failed !== scenario,
    hasError: failed === scenario,
    horizonMonths: scenario.horizonMonths,
    isHypothesis: supposesSomething(scenario),

    simulations: shelf.simulations,
    opened,
    saveError: shelf.error,
    /** Whether what is on screen has drifted from the scenario that was saved. */
    hasUnsavedChanges: opened !== null && !sameScenario(scenario, scenarioOf(opened)),

    open,
    saveAs,
    saveOver,
    remove,

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
    reset: () => {
      setScenario((current) => ({
        ...NO_SCENARIO,
        horizonMonths: current.horizonMonths,
      }));
      setOpenedId(null);
    },
  };
}
