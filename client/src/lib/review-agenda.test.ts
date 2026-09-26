import { describe, expect, it } from "vitest";

import type { FlaggedUpdateResponse } from "@/lib/api/generated/model";
import { groupByProject } from "@/lib/review-agenda";

function raised(over: Partial<FlaggedUpdateResponse> = {}): FlaggedUpdateResponse {
  return {
    update_id: 1,
    project_id: 10,
    project_label: "Portail",
    body: "Le sponsor attend une date.",
    author: { id: 7, display_name: "L. Chen", initials: "LC" },
    published_at: "2026-09-21T09:00:00Z",
    raised_by: { id: 8, display_name: "N. Garo", initials: "NG" },
    flagged_at: "2026-09-22T09:00:00Z",
    ...over,
  };
}

describe("groupByProject", () => {
  it("gathers a project's lines under its name", () => {
    const agenda = groupByProject([
      raised({ update_id: 1 }),
      raised({ update_id: 2, flagged_at: "2026-09-23T09:00:00Z" }),
    ]);

    expect(agenda).toHaveLength(1);
    expect(agenda[0].label).toBe("Portail");
    expect(agenda[0].items.map((one) => one.update_id)).toEqual([1, 2]);
  });

  /**
   * A revue opens on what has waited longest, and the server sends the lines
   * in that order. Two projects raised in turn therefore arrive interleaved:
   * a chapter takes the rank of its first line, which is its oldest.
   */
  it("ranks a project by its oldest line, across interleaved ones", () => {
    const agenda = groupByProject([
      raised({ project_id: 10, update_id: 1, flagged_at: "2026-09-22T09:00:00Z" }),
      raised({
        project_id: 11,
        project_label: "Atlas",
        update_id: 2,
        flagged_at: "2026-09-24T09:00:00Z",
      }),
      raised({ project_id: 10, update_id: 3, flagged_at: "2026-09-26T09:00:00Z" }),
    ]);

    expect(agenda.map((one) => one.label)).toEqual(["Portail", "Atlas"]);
    expect(agenda[0].items.map((one) => one.update_id)).toEqual([1, 3]);
  });

  it("keeps the server's order inside a project", () => {
    const agenda = groupByProject([
      raised({ update_id: 5 }),
      raised({ update_id: 3, flagged_at: "2026-09-25T09:00:00Z" }),
    ]);

    expect(agenda[0].items.map((one) => one.update_id)).toEqual([5, 3]);
  });

  it("answers nothing on an empty agenda", () => {
    expect(groupByProject([])).toEqual([]);
  });
});
