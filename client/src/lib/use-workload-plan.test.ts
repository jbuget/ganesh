import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useWorkloadPlanScreen } from "./use-workload-plan";

/** What the server was last asked, which is what a what-if actually changes. */
const asked = vi.hoisted(() => ({
  horizonMonths: 0,
  order: [] as number[] | undefined,
}));

const missions = vi.hoisted(() => ({
  value: [{ project_id: 10 }, { project_id: 20 }, { project_id: 30 }],
}));

vi.mock("@/lib/api/queries", () => ({
  useWorkloadPlan: (horizonMonths: number, order: number[]) => {
    asked.horizonMonths = horizonMonths;
    asked.order = order;
    return {
      plan: { missions: missions.value, people: [], weeks: [] },
      isLoading: false,
      isError: false,
    };
  },
}));

beforeEach(() => {
  asked.horizonMonths = 0;
  asked.order = [];
});

describe("useWorkloadPlanScreen", () => {
  it("opens on the order the team already decided", () => {
    const { result } = renderHook(() => useWorkloadPlanScreen());

    expect(result.current.isHypothesis).toBe(false);
    expect(asked.order).toEqual([]);
  });

  it("asks the whole projection again on the order moved to", () => {
    const { result } = renderHook(() => useWorkloadPlanScreen());

    act(() => result.current.move(30, 0));

    expect(asked.order).toEqual([30, 10, 20]);
    expect(result.current.isHypothesis).toBe(true);
  });

  it("moves a mission down as readily as up", () => {
    const { result } = renderHook(() => useWorkloadPlanScreen());

    act(() => result.current.move(10, 2));

    expect(asked.order).toEqual([20, 30, 10]);
  });

  it("asks nothing of a mission put back where it was", () => {
    const { result } = renderHook(() => useWorkloadPlanScreen());

    act(() => result.current.move(10, 0));

    expect(result.current.isHypothesis).toBe(false);
  });

  it("ignores a mission the plan does not hold", () => {
    const { result } = renderHook(() => useWorkloadPlanScreen());

    act(() => result.current.move(99, 0));

    expect(result.current.isHypothesis).toBe(false);
  });

  it("comes back to the order of the team when the hypothesis is dropped", () => {
    const { result } = renderHook(() => useWorkloadPlanScreen());

    act(() => result.current.move(30, 0));
    act(() => result.current.reset());

    expect(asked.order).toEqual([]);
    expect(result.current.isHypothesis).toBe(false);
  });

  it("changes how far ahead it looks without losing the hypothesis", () => {
    // Widening the horizon is how one checks whether what did not fit in six
    // months fits in twelve: the scenario under the eye must survive it.
    const { result } = renderHook(() => useWorkloadPlanScreen());

    act(() => result.current.move(30, 0));
    act(() => result.current.setHorizon(12));

    expect(asked.horizonMonths).toBe(12);
    expect(asked.order).toEqual([30, 10, 20]);
  });
});
