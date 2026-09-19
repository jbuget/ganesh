"use client";

import { useCallback, useEffect, useState } from "react";

import {
  deleteSimulation,
  listSimulations,
  saveSimulation,
  updateSimulation,
} from "@/lib/api/generated/planning/planning";
import type { SimulationResponse } from "@/lib/api/generated/model";
import type { Scenario } from "@/lib/planning";

/** A scenario, as the API takes it down. */
function toRequest(name: string, scenario: Scenario) {
  return {
    name,
    horizon_months: scenario.horizonMonths,
    order: scenario.order,
    staffing: scenario.staffing,
  };
}

/** The scenario a saved simulation holds. */
export function scenarioOf(simulation: SimulationResponse): Scenario {
  return {
    horizonMonths: simulation.horizon_months,
    order: simulation.order,
    staffing: simulation.staffing,
  };
}

/**
 * The scenarios the team keeps: reading them, writing them down, dropping them.
 *
 * The list is reloaded after every write rather than patched in place: two
 * people may be saving at once, and a shelf that quietly disagrees with the
 * server is worse than one that takes a round trip to settle.
 */
export function useSimulations() {
  const [simulations, setSimulations] = useState<SimulationResponse[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const response = await listSimulations();
    setSimulations(response.data as SimulationResponse[]);
  }, []);

  useEffect(() => {
    // Read through the promise rather than by awaiting a call in the effect
    // body: React wants an effect to subscribe, not to set state on its way in.
    let alive = true;
    listSimulations().then((response) => {
      if (alive) setSimulations(response.data as SimulationResponse[]);
    });
    return () => {
      alive = false;
    };
  }, []);

  /** Writes a scenario down. Returns it, or null if the name was taken. */
  async function save(name: string, scenario: Scenario) {
    try {
      const response = await saveSimulation(toRequest(name, scenario));
      await refresh();
      setError(null);
      return response.data as SimulationResponse;
    } catch {
      // The one refusal worth wording: two scenarios of the same name would
      // make choosing between them a guess.
      setError(`Une simulation porte déjà le nom « ${name.trim()} ».`);
      return null;
    }
  }

  /** Rewrites a scenario in place, so trying again costs no second row. */
  async function rewrite(simulation: SimulationResponse, scenario: Scenario) {
    const response = await updateSimulation(
      simulation.id,
      toRequest(simulation.name, scenario),
    );
    await refresh();
    return response.data as SimulationResponse;
  }

  async function remove(simulationId: number) {
    await deleteSimulation(simulationId);
    await refresh();
  }

  return {
    simulations,
    error,
    clearError: () => setError(null),
    save,
    rewrite,
    remove,
  };
}
