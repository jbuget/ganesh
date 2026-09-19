import { describe, expect, it } from "vitest";

import type {
  ProjectListItemResponse,
  ProjectResponse,
} from "@/lib/api/generated/model";
import { canBeAttached, canReceive } from "@/lib/mission-attach";

const mission = (project: Partial<ProjectResponse>) =>
  ({ project: { id: 1, kind: "project", ...project } }) as ProjectListItemResponse;

describe("canBeAttached", () => {
  it("picks up a project that belongs to no one", () => {
    expect(canBeAttached(mission({ id: 20 }), 0)).toBe(true);
  });

  it("picks up a work package, which may move to another project", () => {
    expect(
      canBeAttached(mission({ id: 20, kind: "work_package", parent_id: 10 }), 0),
    ).toBe(true);
  });

  it("leaves off-project work alone", () => {
    expect(canBeAttached(mission({ id: 20, kind: "off_project" }), 0)).toBe(false);
  });

  it("leaves a mission carrying sub-projects alone", () => {
    expect(canBeAttached(mission({ id: 20 }), 2)).toBe(false);
  });

  it("leaves a published mission alone", () => {
    expect(canBeAttached(mission({ id: 20, is_published: true }), 0)).toBe(false);
  });
});

describe("canReceive", () => {
  const dragged = mission({ id: 20 });

  it("takes a mission under a project", () => {
    expect(canReceive(mission({ id: 10 }), dragged)).toBe(true);
  });

  it("refuses a work package, which carries nothing itself", () => {
    expect(
      canReceive(mission({ id: 10, kind: "work_package", parent_id: 5 }), dragged),
    ).toBe(false);
  });

  it("refuses off-project work", () => {
    expect(canReceive(mission({ id: 10, kind: "off_project" }), dragged)).toBe(false);
  });

  it("refuses the mission itself", () => {
    expect(canReceive(dragged, dragged)).toBe(false);
  });

  it("refuses the project the mission already belongs to", () => {
    const attached = mission({ id: 20, kind: "work_package", parent_id: 10 });

    expect(canReceive(mission({ id: 10 }), attached)).toBe(false);
  });

  it("receives nothing while nothing is being dragged", () => {
    expect(canReceive(mission({ id: 10 }), null)).toBe(false);
  });
});
