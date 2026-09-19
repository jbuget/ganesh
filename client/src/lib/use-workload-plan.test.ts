import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useWorkloadPlanScreen } from "./use-workload-plan";

/** What the server was last asked: a scenario is only ever a request. */
const asked = vi.hoisted(() => ({ body: null as Record<string, unknown> | null }));

const missions = vi.hoisted(() => ({
  value: [{ project_id: 10 }, { project_id: 20 }, { project_id: 30 }],
}));

vi.mock("@/lib/api/generated/planning/planning", () => ({
  projectWorkload: (body: Record<string, unknown>) => {
    asked.body = body;
    return Promise.resolve({
      data: { missions: missions.value, people: [], weeks: [], summary: {} },
    });
  },
}));

async function aScreen() {
  const { result } = renderHook(() => useWorkloadPlanScreen());
  await waitFor(() => expect(result.current.plan).not.toBeNull());
  return result;
}

beforeEach(() => {
  asked.body = null;
});

describe("useWorkloadPlanScreen", () => {
  it("opens on the order the team already decided", async () => {
    const result = await aScreen();

    expect(result.current.isHypothesis).toBe(false);
    expect(asked.body).toMatchObject({ order: [], staffing: {} });
  });

  describe("reordering", () => {
    it("asks the whole projection again on the order moved to", async () => {
      const result = await aScreen();

      act(() => result.current.move(30, 0));

      await waitFor(() => expect(asked.body?.order).toEqual([30, 10, 20]));
      expect(result.current.isHypothesis).toBe(true);
    });

    it("sends a mission straight to the front", async () => {
      const result = await aScreen();

      act(() => result.current.moveToTop(30));

      await waitFor(() => expect(asked.body?.order).toEqual([30, 10, 20]));
    });

    it("moves a mission one rank down", async () => {
      const result = await aScreen();

      act(() => result.current.moveDown(10));

      await waitFor(() => expect(asked.body?.order).toEqual([20, 10, 30]));
    });

    it("moves a mission one rank up", async () => {
      const result = await aScreen();

      act(() => result.current.moveUp(30));

      await waitFor(() => expect(asked.body?.order).toEqual([10, 30, 20]));
    });

    it("asks nothing of a mission already where it would go", async () => {
      const result = await aScreen();

      act(() => result.current.moveUp(10));

      expect(result.current.isHypothesis).toBe(false);
    });

    it("ignores a mission the plan does not hold", async () => {
      const result = await aScreen();

      act(() => result.current.moveToTop(99));

      expect(result.current.isHypothesis).toBe(false);
    });
  });

  describe("staffing", () => {
    it("supposes a mission is carried by these people", async () => {
      const result = await aScreen();

      act(() => result.current.staff(20, [1, 3]));

      await waitFor(() => expect(asked.body?.staffing).toEqual({ 20: [1, 3] }));
      expect(result.current.isHypothesis).toBe(true);
    });

    it("keeps what was supposed of the other missions", async () => {
      const result = await aScreen();

      act(() => result.current.staff(20, [1]));
      act(() => result.current.staff(30, [2]));

      await waitFor(() => expect(asked.body?.staffing).toEqual({ 20: [1], 30: [2] }));
    });

    it("supposing nobody carries it is a hypothesis like any other", async () => {
      // « Et si on retirait tout le monde ? » is a question worth asking.
      const result = await aScreen();

      act(() => result.current.staff(20, []));

      await waitFor(() => expect(asked.body?.staffing).toEqual({ 20: [] }));
      expect(result.current.isHypothesis).toBe(true);
    });
  });

  describe("dropping the hypothesis", () => {
    it("comes back to the order and the team of the team", async () => {
      const result = await aScreen();

      act(() => result.current.move(30, 0));
      act(() => result.current.staff(20, [1]));
      act(() => result.current.reset());

      await waitFor(() =>
        expect(asked.body).toMatchObject({ order: [], staffing: {} }),
      );
      expect(result.current.isHypothesis).toBe(false);
    });

    it("keeps how far ahead one was looking", async () => {
      // The horizon is not a hypothesis: it is how one is reading.
      const result = await aScreen();

      act(() => result.current.setHorizon(12));
      act(() => result.current.reset());

      await waitFor(() => expect(asked.body?.horizon_months).toBe(12));
    });
  });

  it("changes how far ahead it looks without losing the hypothesis", async () => {
    // Widening the horizon is how one checks whether what did not fit in six
    // months fits in twelve: the scenario under the eye must survive it.
    const result = await aScreen();

    act(() => result.current.move(30, 0));
    await waitFor(() => expect(asked.body?.order).toEqual([30, 10, 20]));

    act(() => result.current.setHorizon(12));

    await waitFor(() => expect(asked.body?.horizon_months).toBe(12));
    expect(asked.body?.order).toEqual([30, 10, 20]);
  });
});
