import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { ProjectSteeringTab } from "./ProjectSteeringTab";
import type { ProjectDetailResponse, ProjectKind } from "@/lib/api/generated/model";

// The pickers ask the server for the team; steering itself does not.
vi.mock("@/lib/api/queries", () => ({ useTeammates: () => ({ teammates: [] }) }));

const detail = (kind: ProjectKind): ProjectDetailResponse =>
  ({
    project: {
      id: 10,
      label: "Portail",
      kind,
      status: "scoping",
      parent_id: kind === "work_package" ? 9 : null,
      is_active: true,
      estimated_days: null,
      category: null,
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

const steering = (kind: ProjectKind) =>
  render(
    <ProjectSteeringTab
      detail={detail(kind)}
      onChange={vi.fn()}
      saveSheet={vi.fn()}
      changePhase={vi.fn()}
      updateFields={vi.fn()}
      addLink={vi.fn()}
      removeLink={vi.fn()}
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
