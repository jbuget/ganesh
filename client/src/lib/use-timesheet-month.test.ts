import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useTimesheetMonth } from "./use-timesheet-month";

const entries = vi.hoisted(() => ({
  addMissionToMonth: vi.fn(),
  clearEntry: vi.fn(),
  removeMissionFromMonth: vi.fn(),
  setEntry: vi.fn(),
}));
const projects = vi.hoisted(() => ({
  useCreateProject: () => ({ mutateAsync: projects.createProject }),
  createProject: vi.fn(),
  createProjectActivity: vi.fn(async () => ({
    status: 201,
    data: { id: 420 },
  })),
}));
const queries = vi.hoisted(() => ({
  grid: { rows: [] as unknown[], is_writable: true } as
    { rows: unknown[]; is_writable: boolean } | undefined,
  me: { id: 1, role: "TEAMMATE" },
  useMonthGrid: () => ({ grid: queries.grid, isLoading: false }),
  useCurrentUser: () => ({ user: queries.me }),
  teammates: [] as { id: number; display_name: string }[],
  useTeammates: () => ({ teammates: queries.teammates }),
  useProjects: () => ({ missions: [], projects: [] }),
  mutationResult: (result: unknown) => result,
}));

vi.mock("@/lib/api/generated/entries/entries", () => entries);
const months = vi.hoisted(() => ({
  validateMonth: vi.fn(),
  reopenMonth: vi.fn(),
}));

vi.mock("@/lib/api/generated/months/months", () => ({
  useValidateMonth: () => ({ mutateAsync: months.validateMonth }),
  useReopenMonth: () => ({ mutateAsync: months.reopenMonth }),
}));
vi.mock("@/lib/api/generated/projects/projects", () => projects);
vi.mock("@/lib/api/queries", () => queries);
vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  projects.createProject.mockResolvedValue({ id: 42 });
  queries.grid = { rows: [], is_writable: true };
  queries.me = { id: 1, role: "TEAMMATE" };
  queries.teammates = [];
  window.history.replaceState(null, "", "/");
});

function month() {
  const { result } = renderHook(() => useTimesheetMonth());
  return result;
}

describe("useTimesheetMonth", () => {
  /**
   * A mission lined up without any time on it used to live in the component's
   * state alone, and a reload wiped it out.
   */
  it("puts a mission on the month server-side, before any time is entered", async () => {
    const screen = month();

    await screen.current.addMission(10, 100);

    expect(entries.addMissionToMonth).toHaveBeenCalledWith(
      { project_id: 10, activity_id: 100, month: screen.current.month },
      undefined,
    );
  });

  it("puts a mission on a colleague's month, not on one's own", async () => {
    const screen = month();
    act(() => screen.current.viewTeammate(7));

    await screen.current.addMission(10, 100);

    expect(entries.addMissionToMonth).toHaveBeenCalledWith(expect.anything(), {
      user_id: 7,
    });
  });

  it("puts a freshly declared project on the month right away", async () => {
    const screen = month();

    await screen.current.declareProject("Portail", "delivery");

    expect(projects.createProject).toHaveBeenCalled();
    // Cut into the trade that was asked for, and the row points at it: a
    // mission carrying none is a row the API refuses every write on, which
    // is exactly what declaring from one's own month exists to avoid.
    expect(projects.createProjectActivity).toHaveBeenCalledWith(42, {
      label: "Delivery",
      nature: "delivery",
      estimated_days: null,
    });
    expect(entries.addMissionToMonth).toHaveBeenCalledWith(
      { project_id: 42, activity_id: 420, month: screen.current.month },
      undefined,
    );
  });

  /**
   * The row now exists server-side even when empty: taking it off must always
   * be asked for, or it would come back on the next reload.
   */
  it("takes a mission off the month server-side, even an empty one", async () => {
    const screen = month();

    await screen.current.removeMission(10, 100);

    expect(entries.removeMissionFromMonth).toHaveBeenCalledWith({
      project_id: 10,
      activity_id: 100,
      month: screen.current.month,
    });
  });
});

describe("the month in the address", () => {
  it("opens the month the address names: a reminder links to the month it speaks of", () => {
    window.history.replaceState(null, "", "?month=2026-03");

    expect(month().current.month).toBe("2026-03-01");
  });

  it("falls back on the month running when the address names none", () => {
    expect(month().current.month).toBe(
      `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, "0")}-01`,
    );
  });

  it("writes the month it moves to, so the month can be shared by a link", () => {
    const screen = month();

    act(() => screen.current.goToPreviousMonth());

    expect(new URLSearchParams(window.location.search).get("month")).toBe(
      screen.current.month.slice(0, 7),
    );
  });

  it("reads the teammate being looked at from the address", () => {
    // A colleague's month is reached by a link, from their panel: the screen
    // must open on them rather than on oneself.
    window.history.replaceState(null, "", "/timesheet?user=7");

    expect(month().current.targetUserId).toBe(7);
    expect(month().current.isOwnMonth).toBe(false);
  });

  it("puts the teammate one switches to in the address", () => {
    const screen = month();

    act(() => screen.current.viewTeammate(7));

    expect(window.location.search).toBe("?user=7");
  });

  it("comes back to one's own month by leaving the address bare", () => {
    window.history.replaceState(null, "", "/timesheet?user=7");
    const screen = month();

    act(() => screen.current.viewTeammate(1));

    expect(window.location.search).toBe("");
  });

  it("keeps the month one is on when switching teammate", () => {
    window.history.replaceState(null, "", "/timesheet?month=2026-08");
    const screen = month();

    act(() => screen.current.viewTeammate(7));

    expect(window.location.search).toBe("?month=2026-08&user=7");
  });
});

/**
 * The matrix of the entry screen, on three dimensions: whose month is shown,
 * what the viewer's role is, and whether the month is validated. The two
 * gestures never cross — validating is about the month being one's own,
 * reopening is about being a manager — and the state is what tells them apart.
 */
describe("who may validate, and who may reopen", () => {
  function screenFor({
    role = "TEAMMATE",
    writable = true,
    viewing,
  }: {
    role?: string;
    writable?: boolean;
    viewing?: number;
  }) {
    queries.me = { id: 1, role };
    queries.grid = { rows: [], is_writable: writable };
    const { result } = renderHook(() => useTimesheetMonth());
    if (viewing !== undefined) act(() => result.current.viewTeammate(viewing));
    return result;
  }

  it("lets anyone validate their own open month, manager or not", () => {
    expect(screenFor({}).current.canValidate).toBe(true);
    expect(screenFor({ role: "MANAGER" }).current.canValidate).toBe(true);
  });

  it("never offers to validate a colleague's month: validation is not delegated", () => {
    expect(screenFor({ viewing: 7 }).current.canValidate).toBe(false);
    expect(screenFor({ role: "MANAGER", viewing: 7 }).current.canValidate).toBe(false);
  });

  it("never offers to validate a month already validated", () => {
    expect(screenFor({ writable: false }).current.canValidate).toBe(false);
  });

  it("lets a manager reopen a validated month, their own as well as a colleague's", () => {
    expect(screenFor({ role: "MANAGER", writable: false }).current.canReopen).toBe(
      true,
    );
    expect(
      screenFor({ role: "MANAGER", writable: false, viewing: 7 }).current.canReopen,
    ).toBe(true);
  });

  it("never lets a teammate reopen a month, not even their own", () => {
    expect(screenFor({ writable: false }).current.canReopen).toBe(false);
    expect(screenFor({ writable: false, viewing: 7 }).current.canReopen).toBe(false);
  });

  it("offers nothing to reopen while the month is still open", () => {
    expect(screenFor({ role: "MANAGER" }).current.canReopen).toBe(false);
  });

  it("offers neither gesture while the grid has not arrived", () => {
    queries.grid = undefined;
    queries.me = { id: 1, role: "MANAGER" };
    const { result } = renderHook(() => useTimesheetMonth());

    expect(result.current.canValidate).toBe(false);
    expect(result.current.canReopen).toBe(false);
  });
});

describe("reopening a month", () => {
  it("reopens the month of the teammate the selector names", async () => {
    queries.me = { id: 1, role: "MANAGER" };
    queries.grid = { rows: [], is_writable: false };
    const { result } = renderHook(() => useTimesheetMonth());
    act(() => result.current.viewTeammate(7));

    await result.current.reopen();

    expect(months.reopenMonth).toHaveBeenCalledWith({
      month: result.current.month,
      params: { user_id: 7 },
    });
  });

  /** No teammate selected means one's own month, which the route still names. */
  it("reopens one's own month under one's own id", async () => {
    queries.me = { id: 1, role: "MANAGER" };
    queries.grid = { rows: [], is_writable: false };
    const { result } = renderHook(() => useTimesheetMonth());

    await result.current.reopen();

    expect(months.reopenMonth).toHaveBeenCalledWith({
      month: result.current.month,
      params: { user_id: 1 },
    });
  });
});

describe("whose month is shown", () => {
  it("names the teammate being looked at, so a dialog can say whose month it is", () => {
    queries.teammates = [
      { id: 1, display_name: "Moi" },
      { id: 7, display_name: "Camille Roy" },
    ];
    const { result } = renderHook(() => useTimesheetMonth());
    act(() => result.current.viewTeammate(7));

    expect(result.current.viewedTeammateName).toBe("Camille Roy");
  });

  it("names nobody on one's own month", () => {
    queries.teammates = [{ id: 1, display_name: "Moi" }];

    expect(
      renderHook(() => useTimesheetMonth()).result.current.viewedTeammateName,
    ).toBe(null);
  });
});

/**
 * Half a day is two clicks on one cell. Written as they came, the second read
 * a cell the first had not come back to yet: one asked for half a day and got
 * a whole one, and the grid sent two writes for the one gesture.
 */
describe("entering time", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  /** Lets the writes go out and run to the end. */
  async function settle() {
    await act(async () => {
      vi.advanceTimersByTime(400);
    });
  }

  it("sends one write for the clicks that make up one gesture", async () => {
    const screen = month();

    act(() => screen.current.setDayValue(10, 100, "2026-09-14", 1));
    act(() => screen.current.setDayValue(10, 100, "2026-09-14", 0.5));
    await settle();

    expect(entries.setEntry).toHaveBeenCalledTimes(1);
    expect(entries.setEntry).toHaveBeenCalledWith(
      { project_id: 10, activity_id: 100, day: "2026-09-14", value: 0.5 },
      undefined,
    );
  });

  it("removes the entry when the cell comes back to empty", async () => {
    const screen = month();

    act(() => screen.current.setDayValue(10, 100, "2026-09-14", 0));
    await settle();

    expect(entries.clearEntry).toHaveBeenCalledWith({
      project_id: 10,
      activity_id: 100,
      day: "2026-09-14",
    });
  });

  /** A write still waiting must go where it was clicked, not where one is. */
  it("writes on the month of the colleague whose cell was clicked", async () => {
    const screen = month();
    act(() => screen.current.viewTeammate(7));

    act(() => screen.current.setDayValue(10, 100, "2026-09-14", 1));
    act(() => screen.current.viewTeammate(1));
    await settle();

    expect(entries.setEntry).toHaveBeenCalledWith(expect.anything(), { user_id: 7 });
  });

  /**
   * The month closes to writes: a cell still waiting would be refused, and the
   * time declared would be lost without a word.
   */
  it("sends what is waiting before the month is validated", async () => {
    const screen = month();
    act(() => screen.current.setDayValue(10, 100, "2026-09-14", 1));

    await act(async () => {
      await screen.current.validate();
    });

    expect(entries.setEntry).toHaveBeenCalled();
    expect(entries.setEntry.mock.invocationCallOrder[0]).toBeLessThan(
      months.validateMonth.mock.invocationCallOrder[0],
    );
  });

  /** A cell still waiting would write itself back onto a row that has gone. */
  it("sends what is waiting before a mission leaves the month", async () => {
    const screen = month();
    act(() => screen.current.setDayValue(10, 100, "2026-09-14", 1));

    await act(async () => {
      await screen.current.removeMission(10, 100);
    });

    expect(entries.setEntry.mock.invocationCallOrder[0]).toBeLessThan(
      entries.removeMissionFromMonth.mock.invocationCallOrder[0],
    );
  });
});
