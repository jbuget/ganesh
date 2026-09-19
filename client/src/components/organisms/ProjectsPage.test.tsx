import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectsPage } from "./ProjectsPage";

const state = vi.hoisted(() => ({
  isLoading: false,
  isManager: false,
  tree: [] as unknown[],
  visible: 0,
  total: 0,
  isExpanded: () => false,
  toggle: vi.fn(),
  refresh: vi.fn(),
  declare: vi.fn(),
  importCsv: vi.fn(),
}));

vi.mock("@/lib/use-projects", () => ({ useProjectsScreen: () => state }));

// The filter bar offers the team: it asks the server for it, the page does not.
vi.mock("@/lib/api/queries", () => ({
  useTeammates: () => ({ teammates: [] }),
}));

/**
 * The panel reads the mission from the server and has its own tests: what is
 * asked here is only whether the page opens it, and on which mission.
 */
vi.mock("@/components/organisms/ProjectPanel", () => ({
  ProjectPanel: ({ projectId }: { projectId: number }) => (
    <aside aria-label={`Mission ${projectId}`} />
  ),
}));

beforeEach(() => {
  vi.clearAllMocks();
  state.declare.mockResolvedValue({ id: 42, label: "Portail" });
});

afterEach(() => {
  // The open panel lives in the address: without clearing it, one test would
  // open the next one's screen.
  window.history.replaceState(null, "", "/");
});

async function declare(label: string) {
  await userEvent.click(screen.getByRole("button", { name: "Déclarer un projet" }));
  await userEvent.type(screen.getByLabelText("Nom du projet"), label);
  await userEvent.click(screen.getByRole("button", { name: "Déclarer" }));
}

describe("ProjectsPage", () => {
  it("declares the project the reference list is missing", async () => {
    render(<ProjectsPage />);

    await declare("Portail");

    expect(state.declare).toHaveBeenCalledWith("Portail", "project");
  });

  /**
   * A name alone declares nothing worth steering: phase, priority, estimate
   * and people are still to be given. The panel is where they are given, so
   * declaring leads there rather than back to a list one would have to search.
   */
  it("opens the mission just declared", async () => {
    render(<ProjectsPage />);

    await declare("Portail");

    expect(await screen.findByLabelText("Mission 42")).toBeInTheDocument();
  });
});
