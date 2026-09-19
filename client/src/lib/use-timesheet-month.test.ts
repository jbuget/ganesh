import { beforeEach, describe, expect, it, vi } from "vitest";
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
}));
const queries = vi.hoisted(() => ({
  grid: { rows: [] as unknown[], is_writable: true },
  useMonthGrid: () => ({ grid: queries.grid, isLoading: false }),
  useCurrentUser: () => ({ user: { id: 1 } }),
  useTeammates: () => ({ teammates: [] }),
  useProjects: () => ({ missions: [], projects: [] }),
  mutationResult: (result: unknown) => result,
}));

vi.mock("@/lib/api/generated/entries/entries", () => entries);
vi.mock("@/lib/api/generated/months/months", () => ({
  useValidateMonth: () => ({ mutateAsync: vi.fn() }),
}));
vi.mock("@/lib/api/generated/projects/projects", () => projects);
vi.mock("@/lib/api/queries", () => queries);
vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  projects.createProject.mockResolvedValue({ id: 42 });
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

    await screen.current.addMission(10);

    expect(entries.addMissionToMonth).toHaveBeenCalledWith(
      { project_id: 10, month: screen.current.month },
      undefined,
    );
  });

  it("puts a mission on a colleague's month, not on one's own", async () => {
    const screen = month();
    act(() => screen.current.viewTeammate(7));

    await screen.current.addMission(10);

    expect(entries.addMissionToMonth).toHaveBeenCalledWith(expect.anything(), {
      user_id: 7,
    });
  });

  it("puts a freshly declared project on the month right away", async () => {
    const screen = month();

    await screen.current.declareProject("Portail");

    expect(projects.createProject).toHaveBeenCalled();
    expect(entries.addMissionToMonth).toHaveBeenCalledWith(
      { project_id: 42, month: screen.current.month },
      undefined,
    );
  });

  /**
   * The row now exists server-side even when empty: taking it off must always
   * be asked for, or it would come back on the next reload.
   */
  it("takes a mission off the month server-side, even an empty one", async () => {
    const screen = month();

    await screen.current.removeMission(10);

    expect(entries.removeMissionFromMonth).toHaveBeenCalledWith({
      project_id: 10,
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
});
