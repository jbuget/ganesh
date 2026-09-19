import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useWorkloadPlanScreen } from "./use-workload-plan";

/** What the server was last asked: a scenario is only ever a request. */
const asked = vi.hoisted(() => ({ body: null as Record<string, unknown> | null }));

const missions = vi.hoisted(() => ({
  value: [{ project_id: 10 }, { project_id: 20 }, { project_id: 30 }],
}));

/** The shelf of saved scenarios, as the server holds it. */
const shelf = vi.hoisted(() => ({
  rows: [] as Record<string, unknown>[],
  nextId: 1,
  taken: [] as string[],
  deleted: [] as number[],
  written: [] as Record<string, unknown>[],
}));

vi.mock("@/lib/api/generated/planning/planning", () => ({
  projectWorkload: (body: Record<string, unknown>) => {
    asked.body = body;
    return Promise.resolve({
      data: { missions: missions.value, people: [], weeks: [], summary: {} },
    });
  },
  listSimulations: () => Promise.resolve({ data: shelf.rows }),
  saveSimulation: (body: Record<string, unknown>) => {
    if (shelf.taken.includes(body.name as string)) {
      return Promise.reject(new Error("409"));
    }
    const row = { id: shelf.nextId++, updated_at: "2026-09-19", ...body };
    shelf.rows = [...shelf.rows, row];
    shelf.written.push(body);
    return Promise.resolve({ data: row });
  },
  updateSimulation: (id: number, body: Record<string, unknown>) => {
    const row = { id, updated_at: "2026-09-19", ...body };
    shelf.rows = shelf.rows.map((r) => (r.id === id ? row : r));
    shelf.written.push(body);
    return Promise.resolve({ data: row });
  },
  deleteSimulation: (id: number) => {
    shelf.deleted.push(id);
    shelf.rows = shelf.rows.filter((r) => r.id !== id);
    return Promise.resolve({ data: undefined });
  },
}));

function aSavedScenario(overrides: Record<string, unknown> = {}) {
  return {
    id: 7,
    name: "Priorité bailleurs",
    horizon_months: 6,
    order: [30, 10, 20],
    staffing: { 30: [1, 2] },
    author_id: 1,
    created_at: "2026-09-19",
    updated_at: "2026-09-19",
    ...overrides,
  };
}

async function aScreen() {
  const { result } = renderHook(() => useWorkloadPlanScreen());
  await waitFor(() => expect(result.current.plan).not.toBeNull());
  return result;
}

beforeEach(() => {
  asked.body = null;
  shelf.rows = [];
  shelf.nextId = 1;
  shelf.taken = [];
  shelf.deleted = [];
  shelf.written = [];
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

  describe("saved simulations", () => {
    it("opens on the order the team decided, with no simulation loaded", async () => {
      shelf.rows = [aSavedScenario()];
      const result = await aScreen();

      await waitFor(() => expect(result.current.simulations).toHaveLength(1));
      expect(result.current.opened).toBeNull();
    });

    it("loading one projects what it supposes", async () => {
      shelf.rows = [aSavedScenario()];
      const result = await aScreen();
      await waitFor(() => expect(result.current.simulations).toHaveLength(1));

      act(() => result.current.open(result.current.simulations[0]));

      await waitFor(() => expect(asked.body?.order).toEqual([30, 10, 20]));
      expect(asked.body?.staffing).toEqual({ 30: [1, 2] });
      expect(result.current.opened?.name).toBe("Priorité bailleurs");
    });

    it("a saved scenario carries the horizon it was read at", async () => {
      shelf.rows = [aSavedScenario({ horizon_months: 12 })];
      const result = await aScreen();
      await waitFor(() => expect(result.current.simulations).toHaveLength(1));

      act(() => result.current.open(result.current.simulations[0]));

      await waitFor(() => expect(asked.body?.horizon_months).toBe(12));
    });

    it("coming back to the team's order closes the simulation", async () => {
      shelf.rows = [aSavedScenario()];
      const result = await aScreen();
      await waitFor(() => expect(result.current.simulations).toHaveLength(1));
      act(() => result.current.open(result.current.simulations[0]));
      await waitFor(() => expect(result.current.opened).not.toBeNull());

      act(() => result.current.open(null));

      await waitFor(() => expect(asked.body?.order).toEqual([]));
      expect(result.current.opened).toBeNull();
    });

    it("writes a scenario down and stays on it", async () => {
      const result = await aScreen();
      act(() => result.current.moveToTop(30));
      await waitFor(() => expect(asked.body?.order).toEqual([30, 10, 20]));

      await act(async () => {
        await result.current.saveAs("Priorité bailleurs");
      });

      expect(shelf.written[0]).toMatchObject({
        name: "Priorité bailleurs",
        order: [30, 10, 20],
      });
      await waitFor(() =>
        expect(result.current.opened?.name).toBe("Priorité bailleurs"),
      );
    });

    it("a name already taken is reported and nothing is kept", async () => {
      shelf.taken = ["Priorité bailleurs"];
      const result = await aScreen();

      await act(async () => {
        expect(await result.current.saveAs("Priorité bailleurs")).toBe(false);
      });

      expect(result.current.saveError).toContain("Priorité bailleurs");
      expect(result.current.opened).toBeNull();
    });

    it("says when what is on screen has drifted from what was saved", async () => {
      shelf.rows = [aSavedScenario()];
      const result = await aScreen();
      await waitFor(() => expect(result.current.simulations).toHaveLength(1));
      act(() => result.current.open(result.current.simulations[0]));
      await waitFor(() => expect(result.current.opened).not.toBeNull());

      expect(result.current.hasUnsavedChanges).toBe(false);

      act(() => result.current.staff(10, [3]));

      await waitFor(() => expect(result.current.hasUnsavedChanges).toBe(true));
    });

    it("rewriting the open scenario settles it again", async () => {
      shelf.rows = [aSavedScenario()];
      const result = await aScreen();
      await waitFor(() => expect(result.current.simulations).toHaveLength(1));
      act(() => result.current.open(result.current.simulations[0]));
      await waitFor(() => expect(result.current.opened).not.toBeNull());
      act(() => result.current.staff(10, [3]));
      await waitFor(() => expect(result.current.hasUnsavedChanges).toBe(true));

      await act(async () => {
        await result.current.saveOver();
      });

      expect(shelf.written[0]).toMatchObject({ name: "Priorité bailleurs" });
      await waitFor(() => expect(result.current.hasUnsavedChanges).toBe(false));
    });

    it("dropping a scenario takes it off the shelf", async () => {
      shelf.rows = [aSavedScenario()];
      const result = await aScreen();
      await waitFor(() => expect(result.current.simulations).toHaveLength(1));

      await act(async () => {
        await result.current.remove(7);
      });

      expect(shelf.deleted).toEqual([7]);
      await waitFor(() => expect(result.current.simulations).toHaveLength(0));
    });

    it("says nothing would be lost by walking away from an untouched plan", async () => {
      const result = await aScreen();

      expect(result.current.hasWorkToLose).toBe(false);
    });

    it("counts a hypothesis nobody wrote down as work to lose", async () => {
      const result = await aScreen();

      act(() => result.current.moveToTop(30));

      await waitFor(() => expect(result.current.hasWorkToLose).toBe(true));
    });

    it("counts a saved scenario one has since changed as work to lose", async () => {
      shelf.rows = [aSavedScenario()];
      const result = await aScreen();
      await waitFor(() => expect(result.current.simulations).toHaveLength(1));

      act(() => result.current.open(result.current.simulations[0]));
      await waitFor(() => expect(result.current.opened).not.toBeNull());
      expect(result.current.hasWorkToLose).toBe(false);

      act(() => result.current.staff(10, [3]));

      await waitFor(() => expect(result.current.hasWorkToLose).toBe(true));
    });

    it("dropping the one being read leaves the plan on it", async () => {
      // What is on screen is still a legitimate question; it is simply no
      // longer written down anywhere.
      shelf.rows = [aSavedScenario()];
      const result = await aScreen();
      await waitFor(() => expect(result.current.simulations).toHaveLength(1));
      act(() => result.current.open(result.current.simulations[0]));
      await waitFor(() => expect(asked.body?.order).toEqual([30, 10, 20]));

      await act(async () => {
        await result.current.remove(7);
      });

      await waitFor(() => expect(result.current.opened).toBeNull());
      expect(asked.body?.order).toEqual([30, 10, 20]);
      expect(result.current.isHypothesis).toBe(true);
    });
  });
});
