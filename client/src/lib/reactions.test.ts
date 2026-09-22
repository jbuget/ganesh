import { describe, expect, it } from "vitest";

import { Reaction } from "@/lib/api/generated/model";
import { glyphOf, labelOf, REACTIONS, whoReacted } from "@/lib/reactions";

describe("the signs one may leave", () => {
  it("draws every sign the API declares", () => {
    expect(REACTIONS.map((one) => one.reaction)).toEqual(Object.values(Reaction));
  });

  it("gives each one a glyph and a French label", () => {
    expect(glyphOf(Reaction.hooray)).toBe("🎉");
    expect(labelOf(Reaction.hooray)).toBe("Bravo");
  });
});

describe("who reacted", () => {
  it("names one person", () => {
    expect(whoReacted(["L. Chen"])).toBe("L. Chen");
  });

  it("joins two with « et »", () => {
    expect(whoReacted(["L. Chen", "N. Garo"])).toBe("L. Chen et N. Garo");
  });

  it("separates the middle ones with commas", () => {
    expect(whoReacted(["A", "B", "C"])).toBe("A, B et C");
  });

  it("counts the rest beyond four", () => {
    expect(whoReacted(["A", "B", "C", "D", "E"])).toBe("A, B, C, D et 1 autre");
    expect(whoReacted(["A", "B", "C", "D", "E", "F"])).toBe("A, B, C, D et 2 autres");
  });

  it("says nothing of nobody", () => {
    expect(whoReacted([])).toBe("");
  });
});
