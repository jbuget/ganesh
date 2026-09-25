import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectsPage } from "./ProjectsPage";

const state = vi.hoisted(() => ({
  isLoading: false,
  isManager: false,
  mayWrite: true,
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

/**
 * A steering meeting opens on the whole panorama, then works on four columns.
 * What is asked here is the whole chain: the choice made in the bar, the
 * column gone from the table.
 */
describe("the columns one puts away", () => {
  const mission = {
    project: {
      id: 1,
      label: "Portail",
      kind: "project",
      status: "development",
      priority: null,
      category: null,
      estimated_days: null,
      parent_id: null,
      is_active: true,
      is_published: false,
      go_live_date: null,
    },
    leads: [],
    contributors: [],
    delivered_days: 0,
    cost: { build_days: 0, run_days: 0, estimated_days: null },
    tree_cost: { build_days: 0, run_days: 0, estimated_days: null },
    comments: 0,
    latest_update: null,
    links: [],
    departments: [],
  };

  beforeEach(() => {
    state.tree = [{ mission, workPackages: [] }];
  });

  afterEach(() => {
    state.tree = [];
  });

  const columnsMenu = async () => {
    await userEvent.click(screen.getByRole("button", { name: /Colonnes/ }));
    return within(screen.getByRole("dialog"));
  };

  it("shows the whole panorama to start with", () => {
    render(<ProjectsPage />);

    expect(
      within(screen.getByRole("table")).getByText("Catégorie"),
    ).toBeInTheDocument();
  });

  it("drops from the table the column put away", async () => {
    render(<ProjectsPage />);

    const menu = await columnsMenu();
    await userEvent.click(menu.getByRole("button", { name: "Catégorie" }));

    expect(within(screen.getByRole("table")).queryByText("Catégorie")).toBeNull();
  });

  it("brings the whole panorama back at once", async () => {
    render(<ProjectsPage />);

    const menu = await columnsMenu();
    await userEvent.click(menu.getByRole("button", { name: "Catégorie" }));
    await userEvent.click(menu.getByRole("button", { name: "Tout afficher" }));

    expect(
      within(screen.getByRole("table")).getByText("Catégorie"),
    ).toBeInTheDocument();
  });
});

describe("ProjectsPage, read by a guest", () => {
  it("offers no way to add to the reference list", () => {
    state.mayWrite = false;
    render(<ProjectsPage />);

    expect(screen.queryByRole("button", { name: "Déclarer un projet" })).toBeNull();
    state.mayWrite = true;
  });

  it("still offers the export: reading the list out is reading it", () => {
    state.mayWrite = false;
    render(<ProjectsPage />);

    expect(screen.getByRole("button", { name: /Exporter/ })).toBeInTheDocument();
    state.mayWrite = true;
  });
});
