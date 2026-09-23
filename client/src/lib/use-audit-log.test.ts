import { describe, expect, it } from "vitest";

import { asQuery } from "@/lib/use-audit-log";
import { NO_FILTER } from "@/lib/audit-filters";

describe("asQuery", () => {
  /**
   * An empty list of gestures means « none of them » to the API, which is
   * right for a reader who unticked everything and wrong for one who never
   * opened the picker. Untouched criteria are therefore left out entirely.
   */
  it("asks for the whole register when nothing is filtered", () => {
    expect(asQuery(NO_FILTER)).toEqual({ limit: 50, offset: 0 });
  });

  it("names the gestures that were ticked", () => {
    expect(asQuery({ ...NO_FILTER, actions: ["project.delete"] })).toMatchObject({
      action: ["project.delete"],
    });
  });

  it("sends the period as days, which is what the API reads them as", () => {
    expect(
      asQuery({ ...NO_FILTER, fromDay: "2026-09-01", toDay: "2026-09-30" }),
    ).toMatchObject({ from_day: "2026-09-01", to_day: "2026-09-30" });
  });

  it("sends the person as the number the register holds", () => {
    expect(asQuery({ ...NO_FILTER, actorIds: ["7"] })).toMatchObject({ actor_id: 7 });
  });

  it("leaves out a criterion that was cleared again", () => {
    const query = asQuery({ ...NO_FILTER, fromDay: "" });

    expect(query).not.toHaveProperty("from_day");
    expect(query).not.toHaveProperty("action");
  });
});
