import { describe, expect, it } from "vitest";

import {
  assignedMissionIds,
  availableMissions,
  missionsToDeclare,
  missionAnswers,
  offeredMissions,
  rowKey,
  type OfferedMission,
} from "./missions";
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
  /**
   * The database sorts under its own collation, which files « Évènementiel »
   * after « Support » — a French reader finds it nowhere near where they look.
   */
  it("orders each group as French reads, accents included", () => {
    const accented = [
      project(1, "Support", "off_project"),
      project(2, "Évènementiel / communication", "off_project"),
      project(3, "Absences", "off_project"),
      project(4, "Étude d'implantation", "project"),
      project(5, "Formation", "project"),
    ];

    const { projectMissions, offProject } = availableMissions(accented, [], []);

    expect(offProject.map((m) => m.label)).toEqual([
      "Absences",
      "Évènementiel / communication",
      "Support",
    ]);
    expect(projectMissions.map((m) => m.label)).toEqual([
      "Étude d'implantation",
      "Formation",
    ]);
  });

  it("separates projects and work packages from off-project work", () => {
    const { projectMissions, offProject } = availableMissions(PROJECTS, [], []);

    expect(projectMissions.map((p) => p.label)).toEqual(["Lot 1", "Portail bailleurs"]);
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
    // A mission is declared on through its activities, so a mission carrying
    // none offers nothing — every fixture needs one to be offered at all.
    activities:
      project.kind === "off_project"
        ? []
        : [
            {
              id: project.id * 100,
              project_id: project.id,
              label: "Développement",
              nature: "development",
              estimated_days: null,
              is_active: true,
              entries: 0,
            },
          ],
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

    expect(mine.map((p) => p.label)).toEqual(["Absences", "Portail bailleurs"]);
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
    // One line per trade, because that is what a day is declared under.
    expect(missionsToDeclare(MISSIONS, 7, []).map((row) => row.projectLabel)).toEqual([
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

describe("what the selector offers", () => {
  const watom = {
    project: { id: 7, label: "Watom", kind: "project", is_active: true },
    activities: [
      { id: 700, label: "Développement", nature: "development", is_active: true },
      { id: 701, label: "Design", nature: "design", is_active: true },
      {
        id: 702,
        label: "Chefferie de projet",
        nature: "project_management",
        is_active: true,
      },
    ],
  } as unknown as ProjectListItemResponse;

  const leave = {
    project: { id: 9, label: "Congés", kind: "off_project", is_active: true },
    activities: [],
  } as unknown as ProjectListItemResponse;

  it("lists missions, not the pairs", () => {
    const offered = offeredMissions([watom], []);

    expect(offered).toHaveLength(1);
    expect(offered[0].projectLabel).toBe("Watom");
    expect(offered[0].activities.map((a) => a.label)).toEqual([
      "Chefferie de projet",
      "Design",
      "Développement",
    ]);
  });

  it("drops the trades already on the month, keeping the mission", () => {
    // A developer standing in for the project manager: one trade taken must
    // not take the mission away.
    const offered = offeredMissions([watom], [rowKey(7, 700)]);

    expect(offered[0].activities.map((a) => a.label)).toEqual([
      "Chefferie de projet",
      "Design",
    ]);
  });

  it("drops the mission once every trade is taken", () => {
    const every = [rowKey(7, 700), rowKey(7, 701), rowKey(7, 702)];

    expect(offeredMissions([watom], every)).toEqual([]);
  });

  it("drops a mission nobody has cut up: nothing can be declared on it", () => {
    const bare = {
      project: { id: 8, label: "Neuf", kind: "project", is_active: true },
      activities: [],
    } as unknown as ProjectListItemResponse;

    expect(offeredMissions([bare], [])).toEqual([]);
  });

  it("offers off-project work as itself, carrying no trade", () => {
    const offered = offeredMissions([leave], []);

    expect(offered[0].activities).toEqual([]);
    expect(offered[0].kind).toBe("off_project");
  });

  it("drops off-project work once it is on the month", () => {
    expect(offeredMissions([leave], [rowKey(9, null)])).toEqual([]);
  });

  it("leaves an archived mission out", () => {
    const archived = {
      project: { id: 10, label: "Ancien", kind: "project", is_active: false },
      activities: [{ id: 1000, label: "Développement", is_active: true }],
    } as unknown as ProjectListItemResponse;

    expect(offeredMissions([archived], [])).toEqual([]);
  });

  it("leaves an archived trade out", () => {
    const withArchived = {
      project: { id: 11, label: "Mixte", kind: "project", is_active: true },
      activities: [
        { id: 1100, label: "Développement", is_active: true },
        { id: 1101, label: "Design", is_active: false },
      ],
    } as unknown as ProjectListItemResponse;

    expect(
      offeredMissions([withArchived], [])[0].activities.map((a) => a.label),
    ).toEqual(["Développement"]);
  });
});

describe("what the search reads", () => {
  const mission = {
    projectId: 1,
    projectLabel: "Contrôle de la longueur du câblage posé",
    kind: "project",
    activities: [{ id: 100, label: "Chefferie de projet" }],
  } as OfferedMission;

  it("finds a mission by its name, which is what one types", () => {
    expect(missionAnswers(mission, "Contrôle")).toBe(true);
  });

  it("ignores accents, as every other search in the application does", () => {
    expect(missionAnswers(mission, "Controle")).toBe(true);
    expect(missionAnswers(mission, "cablage")).toBe(true);
  });

  it("ignores case", () => {
    expect(missionAnswers(mission, "CONTRÔLE")).toBe(true);
  });

  it("says no to what the name does not carry", () => {
    expect(missionAnswers(mission, "extranet")).toBe(false);
  });

  it("answers everything to an empty query", () => {
    expect(missionAnswers(mission, "   ")).toBe(true);
  });
});
