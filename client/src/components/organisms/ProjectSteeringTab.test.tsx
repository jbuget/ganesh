import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { ProjectSteeringTab } from "./ProjectSteeringTab";
import type {
  ProjectCategory,
  ProjectDetailResponse,
  ProjectKind,
} from "@/lib/api/generated/model";

// The pickers ask the server for the team; steering itself does not.
vi.mock("@/lib/api/queries", () => ({ useTeammates: () => ({ teammates: [] }) }));

// The sheet reads what the mission is cut into as soon as it opens. Left
// alone, the call reaches a relative URL that no test server answers — which
// passes on a machine where the API happens to be running, and nowhere else.
vi.mock("@/lib/use-project-activities", () => ({
  useProjectActivities: () => ({
    activities: [],
    isLoading: false,
    add: vi.fn(),
    change: vi.fn(),
    archive: vi.fn(),
    remove: vi.fn(),
    unarchive: vi.fn(),
  }),
}));

const detail = (
  kind: ProjectKind,
  category: ProjectCategory | null = null,
): ProjectDetailResponse =>
  ({
    project: {
      id: 10,
      label: "Portail",
      kind,
      status: "scoping",
      parent_id: kind === "work_package" ? 9 : null,
      is_active: true,
      estimated_days: null,
      category,
      priority: null,
      business_contacts: null,
      description: null,
    },
    departments: [],
    links: [],
    phases: [],
    leads: [],
    contributors: [],
    consumed_days: 0,
    contributions: [],
    sub_projects: [],
  }) as unknown as ProjectDetailResponse;

const steering = (kind: ProjectKind, category: ProjectCategory | null = null) =>
  render(
    <ProjectSteeringTab
      editable
      detail={detail(kind, category)}
      onChange={vi.fn()}
      saveSheet={vi.fn()}
      changePhase={vi.fn()}
      updateFields={vi.fn()}
      addSubProject={vi.fn()}
    />,
  );

describe("ProjectSteeringTab", () => {
  it("carries the sub-projects of a project", () => {
    steering("project");

    expect(screen.getByText("Sous-projets")).toBeInTheDocument();
  });

  /**
   * The hierarchy stops at two levels, and off-project work carries nothing:
   * the server refuses both. Offering the section anyway would be offering a
   * move that comes back as an error.
   */
  it.each([["work_package"], ["off_project"]] as const)(
    "carries none on %s",
    (kind) => {
      steering(kind);

      expect(screen.queryByText("Sous-projets")).toBeNull();
    },
  );
});

describe("the strategic axis of a mission", () => {
  it("is chosen on a project", () => {
    steering("project");

    expect(
      screen.getByRole("button", { name: "Changer la catégorie" }),
    ).toBeInTheDocument();
  });

  /**
   * The axis qualifies the product, not a slice of it: a work package reads
   * the one its project carries, and changing it means changing the project's
   * — for the project and all its packages at once.
   */
  it("is read, not chosen, on a work package", () => {
    steering("work_package", "innovate_differentiate");

    expect(screen.queryByRole("button", { name: "Changer la catégorie" })).toBeNull();
    expect(screen.getByText("Innover & différencier")).toBeInTheDocument();
  });

  it("says on a work package where it is defined", () => {
    steering("work_package", "innovate_differentiate");

    expect(screen.getByRole("link", { name: "Définie sur le projet" })).toHaveAttribute(
      "href",
      "/projects/9",
    );
  });

  it("sends a work package to its project when the project has none", () => {
    steering("work_package");

    expect(screen.getByText("Aucune")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "À définir sur le projet" }),
    ).toHaveAttribute("href", "/projects/9");
  });
});
