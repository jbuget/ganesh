import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { NO_HIDDEN_COLUMN, hiddenColumns, tableWidth } from "@/lib/mission-columns";
import { NO_SORT } from "@/lib/mission-sort";
import type { ProjectNode } from "@/lib/project-tree";

import { MissionsTable } from "./MissionsTable";

const NOW = new Date("2026-09-17T12:00:00Z");

const cost = {
  build_days: 0,
  run_days: 0,
  estimated_days: null,
  monthly_run_rate: null,
  has_overrun: false,
};

const mission = (id: number, label: string, kind = "project") =>
  ({
    project: {
      id,
      label,
      kind,
      status: "development",
      priority: null,
      category: null,
      estimated_days: null,
      parent_id: null,
      is_active: true,
    },
    leads: [],
    contributors: [],
    delivered_days: 0,
    cost,
    tree_cost: cost,
    comments: 0,
    latest_update: null,
    links: [],
  }) as unknown as ProjectListItemResponse;

const node = (
  id: number,
  label: string,
  workPackages: ProjectListItemResponse[] = [],
): ProjectNode => ({ mission: mission(id, label), workPackages });

function table(over: Partial<Parameters<typeof MissionsTable>[0]> = {}) {
  const props = {
    tree: [node(1, "Portail")],
    sorted: NO_SORT,
    onSort: vi.fn(),
    isExpanded: () => false,
    onToggle: vi.fn(),
    now: NOW,
    onOpen: vi.fn(),
    onOpenThread: vi.fn(),
    ...over,
  };
  render(<MissionsTable {...props} />);
  return props;
}

describe("MissionsTable", () => {
  it("heads every column the reader compares on", () => {
    table();

    for (const title of [
      "Projet",
      "Phase",
      "Priorité",
      "Catégorie",
      "Build",
      "Run",
      "Référents",
      "Intervenants",
      "Liens",
    ]) {
      expect(screen.getByText(title)).toBeInTheDocument();
    }
  });

  it("draws the missions it is given, in the order it is given them", () => {
    table({ tree: [node(1, "Portail"), node(2, "Extranet")] });

    const names = screen.getAllByRole("button", { name: /Portail|Extranet/ });
    expect(names.map((button) => button.textContent)).toEqual(["Portail", "Extranet"]);
  });

  it("keeps a project's work packages folded until it is expanded", () => {
    table({ tree: [node(1, "Portail", [mission(2, "Lot 1", "work_package")])] });

    expect(screen.queryByText("Lot 1")).toBeNull();
  });

  it("shows the work packages of an expanded project", () => {
    table({
      tree: [node(1, "Portail", [mission(2, "Lot 1", "work_package")])],
      isExpanded: () => true,
    });

    expect(screen.getByText("Lot 1")).toBeInTheDocument();
  });

  it("asks to fold rather than deciding for itself", () => {
    const { onToggle } = table({
      tree: [node(1, "Portail", [mission(2, "Lot 1", "work_package")])],
    });

    fireEvent.click(screen.getByRole("button", { name: /sous-projet de Portail/ }));

    expect(onToggle).toHaveBeenCalledWith(1);
  });

  it("asks to sort on the column whose heading was clicked", () => {
    const { onSort } = table();

    fireEvent.click(screen.getByText("Build"));

    expect(onSort).toHaveBeenCalledWith("build");
  });

  it("opens the mission whose row was clicked", () => {
    const { onOpen } = table();

    fireEvent.click(screen.getByText("Portail"));

    expect(onOpen).toHaveBeenCalledWith(1);
  });
});

/**
 * A steering meeting opens on the whole panorama, then works on four columns.
 * The table draws what it is asked to draw, and asks nothing about why.
 */
describe("the columns put away", () => {
  it("shows the whole panorama when nothing is put away", () => {
    table();

    expect(screen.getByText("Catégorie")).toBeInTheDocument();
  });

  it("drops the heading of a column put away", () => {
    table({ hidden: hiddenColumns(["category"]) });

    expect(screen.queryByText("Catégorie")).toBeNull();
  });

  it("drops it from the rows too, not only from the heading", () => {
    const withCategory = mission(1, "Portail");
    withCategory.project.category = "innovate_differentiate";

    table({
      tree: [{ mission: withCategory, workPackages: [] }],
      hidden: hiddenColumns(["category"]),
    });

    expect(screen.queryByText("Innover & différencier")).toBeNull();
  });

  it("keeps the two columns a row is read by, whatever is put away", () => {
    table({
      hidden: hiddenColumns([
        "phase",
        "priority",
        "category",
        "build",
        "run",
        "leads",
        "contributors",
        "links",
      ]),
    });

    expect(screen.getByText("Projet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Portail" })).toBeInTheDocument();
  });

  /**
   * `table-fixed` shares out whatever the table is given: left at its full
   * span, the remaining columns would stretch instead of the list drawing
   * itself narrower.
   */
  it("draws the table narrower by what the column put away was taking", () => {
    table({ hidden: hiddenColumns(["category"]) });

    const width = Number.parseInt(screen.getByRole("table").style.width, 10);
    expect(width).toBeLessThan(tableWidth(NO_HIDDEN_COLUMN));
  });
});

describe("MissionsTable — moving a mission under a project", () => {
  it("offers no handle while the screen asks for no move", () => {
    table();

    expect(screen.queryByRole("button", { name: /Déplacer/ })).toBeNull();
  });

  it("offers a handle on a mission that may become a slice of a project", () => {
    table({ onAttach: vi.fn() });

    expect(
      screen.getByRole("button", { name: "Déplacer Portail" }),
    ).toBeInTheDocument();
  });

  it("offers none on a mission that already carries sub-projects", () => {
    table({
      tree: [node(1, "Portail", [mission(2, "Lot 1", "work_package")])],
      onAttach: vi.fn(),
    });

    expect(screen.queryByRole("button", { name: "Déplacer Portail" })).toBeNull();
  });

  it("offers one on a work package, which may move to another project", () => {
    table({
      tree: [node(1, "Portail", [mission(2, "Lot 1", "work_package")])],
      isExpanded: () => true,
      onAttach: vi.fn(),
    });

    expect(screen.getByRole("button", { name: "Déplacer Lot 1" })).toBeInTheDocument();
  });

  it("offers none on off-project work", () => {
    table({
      tree: [{ mission: mission(3, "Absences", "off_project"), workPackages: [] }],
      onAttach: vi.fn(),
    });

    expect(screen.queryByRole("button", { name: "Déplacer Absences" })).toBeNull();
  });
});
