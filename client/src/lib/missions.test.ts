import { describe, expect, it } from "vitest";

import { assignedMissionIds, availableMissions, missionsToDeclare } from "./missions";
import type {
  ProjectListItemResponse,
  ProjectResponse,
} from "@/lib/api/generated/model";

const project = (id: number, label: string, kind: string): ProjectResponse =>
  ({
    id,
    label,
    kind,
    status: null,
    parent_id: null,
    is_active: true,
    estimated_days: null,
    is_syncable_to_monday: false,
  }) as ProjectResponse;

const PROJECTS = [
  project(1, "Portail bailleurs", "project"),
  project(2, "Absences", "off_project"),
  project(3, "Lot 1", "work_package"),
];

describe("availableMissions", () => {
  it("separates projects and work packages from off-project work", () => {
    const { projectMissions, offProject } = availableMissions(PROJECTS, [], []);

    expect(projectMissions.map((p) => p.label)).toEqual(["Portail bailleurs", "Lot 1"]);
    expect(offProject.map((p) => p.label)).toEqual(["Absences"]);
  });

  it("rules out missions already in the grid", () => {
    const { projectMissions } = availableMissions(PROJECTS, [1], []);

    expect(projectMissions.map((p) => p.label)).toEqual(["Lot 1"]);
  });

  it("may have nothing left to offer", () => {
    const { projectMissions, offProject } = availableMissions(PROJECTS, [1, 2, 3], []);

    expect(projectMissions).toEqual([]);
    expect(offProject).toEqual([]);
  });

  it("does not change the list received", () => {
    const copy = [...PROJECTS];
    availableMissions(PROJECTS, [1], []);

    expect(PROJECTS).toEqual(copy);
  });
});

const listed = (
  project: ProjectResponse,
  contributors: number[],
  leads: number[] = [],
): ProjectListItemResponse =>
  ({
    project,
    contributors: contributors.map((id) => ({
      id,
      display_name: `U${id}`,
      initials: `U${id}`,
    })),
    leads: leads.map((id) => ({ id, display_name: `U${id}`, initials: `U${id}` })),
  }) as ProjectListItemResponse;

const MISSIONS = [
  listed(PROJECTS[0], [7, 9]),
  listed(PROJECTS[1], []),
  listed(PROJECTS[2], [], [7]),
];

describe("assignedMissionIds", () => {
  it("keeps the missions one contributes to", () => {
    expect(assignedMissionIds(MISSIONS, 7)).toEqual([1]);
  });

  it("does not count being a lead: answering for a mission is not spending days on it", () => {
    expect(assignedMissionIds(MISSIONS, 7)).not.toContain(3);
  });

  it("has nothing to say about nobody", () => {
    expect(assignedMissionIds(MISSIONS, null)).toEqual([]);
  });
});

describe("availableMissions", () => {
  it("puts the missions one contributes to in a group of their own", () => {
    const { mine, projectMissions, offProject } = availableMissions(
      PROJECTS,
      [],
      [1, 2],
    );

    expect(mine.map((p) => p.label)).toEqual(["Portail bailleurs", "Absences"]);
    // A mission belongs to one group only: offered twice, it would read as two.
    expect(projectMissions.map((p) => p.label)).toEqual(["Lot 1"]);
    expect(offProject).toEqual([]);
  });

  it("still rules out what the grid already carries, assigned or not", () => {
    const { mine } = availableMissions(PROJECTS, [1], [1, 3]);

    expect(mine.map((p) => p.label)).toEqual(["Lot 1"]);
  });
});

describe("missionsToDeclare", () => {
  it("names what one contributes to with nothing declared on it", () => {
    expect(missionsToDeclare(MISSIONS, 7, []).map((p) => p.label)).toEqual([
      "Portail bailleurs",
    ]);
  });

  it("says nothing about a mission already in the grid", () => {
    expect(missionsToDeclare(MISSIONS, 7, [1])).toEqual([]);
  });

  it("says nothing when one contributes to nothing", () => {
    expect(missionsToDeclare(MISSIONS, 42, [])).toEqual([]);
  });
});
