import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";

import { useProjectDetail } from "./use-project-detail";

const api = vi.hoisted(() => ({
  getProjectDetail: vi.fn(),
  archiveProject: vi.fn(),
  unarchiveProject: vi.fn(),
  updateProject: vi.fn(),
  updateProjectDetail: vi.fn(),
  updateProjectDescription: vi.fn(),
  changeProjectStatus: vi.fn(),
  addProjectLink: vi.fn(),
  removeProjectLink: vi.fn(),
  createProject: vi.fn(),
}));

vi.mock("@/lib/api/generated/projects/projects", () => api);

beforeEach(() => {
  vi.clearAllMocks();
  for (const call of Object.values(api)) call.mockResolvedValue({ data: {} });
  api.getProjectDetail.mockResolvedValue({ data: { project: { id: 7 } } });
});

async function sheet(onWrite?: () => void | Promise<void>) {
  const { result } = renderHook(() => useProjectDetail(7, onWrite));
  await waitFor(() => expect(result.current.detail).not.toBeNull());
  return result;
}

describe("useProjectDetail", () => {
  /**
   * The panel opens over a table that already shows the same mission. Whatever
   * one changes here, the row behind must say it too: a phase, a priority, a
   * link added, an archiving. The screen is told after every write, and it is
   * the only thing that keeps the two from drifting apart.
   */
  it.each([
    [
      "the phase",
      (s: Awaited<ReturnType<typeof sheet>>) => s.current.changePhase("scoping"),
    ],
    [
      "a field",
      (s: Awaited<ReturnType<typeof sheet>>) =>
        s.current.updateFields({ priority: "high" }),
    ],
    [
      "the label",
      (s: Awaited<ReturnType<typeof sheet>>) => s.current.rename("Portail"),
    ],
    [
      "the sheet",
      (s: Awaited<ReturnType<typeof sheet>>) =>
        s.current.saveSheet(["operations"], "Nino"),
    ],
    [
      "the description",
      (s: Awaited<ReturnType<typeof sheet>>) =>
        s.current.saveDescription("## Problème"),
    ],
    [
      "a link added",
      (s: Awaited<ReturnType<typeof sheet>>) =>
        s.current.addLink("Le dépôt", "https://github.com/waat", null),
    ],
    [
      "a link removed",
      (s: Awaited<ReturnType<typeof sheet>>) => s.current.removeLink(3),
    ],
    [
      "a sub-project added",
      (s: Awaited<ReturnType<typeof sheet>>) => s.current.addSubProject("Reprise"),
    ],
    ["archiving", (s: Awaited<ReturnType<typeof sheet>>) => s.current.archive()],
    ["unarchiving", (s: Awaited<ReturnType<typeof sheet>>) => s.current.unarchive()],
  ])("tells the screen it came from when %s changes", async (_what, change) => {
    const notify = vi.fn();
    const result = await sheet(notify);

    await act(async () => {
      await change(result);
    });

    expect(notify).toHaveBeenCalledTimes(1);
  });

  /**
   * The hierarchy stops at two levels, and the server refuses anything else:
   * what is created here is a work package of the mission one is looking at,
   * at the phase every mission starts from.
   */
  it("attaches a sub-project to the mission one is on", async () => {
    const result = await sheet();

    await act(async () => {
      await result.current.addSubProject("Reprise");
    });

    expect(api.createProject).toHaveBeenCalledWith({
      label: "Reprise",
      kind: "work_package",
      status: "exploration",
      parent_id: 7,
    });
  });

  /**
   * Archiving a project cut into packages says what becomes of them in the
   * same call: the server refuses the exit otherwise.
   */
  it("carries what becomes of the sub-projects into the archiving", async () => {
    const result = await sheet();

    await act(async () => {
      await result.current.archive("detach");
    });

    expect(api.archiveProject).toHaveBeenCalledWith(7, { sub_projects: "detach" });
  });

  it("asks nothing of the packages when the mission carries none", async () => {
    const result = await sheet();

    await act(async () => {
      await result.current.archive();
    });

    expect(api.archiveProject).toHaveBeenCalledWith(7, { sub_projects: null });
  });

  it("reads the mission back from the server after a write", async () => {
    const result = await sheet();

    await act(async () => {
      await result.current.updateFields({ priority: "critical" });
    });

    // Once on opening, once after the write: the screen never shows anything
    // other than what the database holds.
    expect(api.getProjectDetail).toHaveBeenCalledTimes(2);
  });
});
