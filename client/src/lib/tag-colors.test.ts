import { describe, expect, it } from "vitest";

import { TagColor } from "@/lib/api/generated/model";
import { TAG_COLORS, tagColorLabel, tagMark } from "./tag-colors";

describe("the palette of tags", () => {
  it("draws every colour the API declares, in the order it declares them", () => {
    expect(TAG_COLORS.map((color) => color.value)).toEqual(Object.values(TagColor));
  });

  it("gives each colour a mark of its own", () => {
    const marks = TAG_COLORS.map((color) => color.mark);

    expect(new Set(marks).size).toBe(marks.length);
  });

  it("spells every mark out in full, for Tailwind to find it", () => {
    for (const { mark } of TAG_COLORS) expect(mark).toMatch(/^bg-[a-z]+-\d{3}$/);
  });

  it("reads the mark of a colour", () => {
    expect(tagMark(TagColor.violet)).toBe("bg-violet-500");
  });

  it("falls back to grey on a colour it does not know yet", () => {
    expect(tagMark("chartreuse" as TagColor)).toBe("bg-slate-400");
  });

  it("says a colour in French", () => {
    expect(tagColorLabel("red")).toBe("Rouge");
    expect(tagColorLabel("lime")).toBe("Citron vert");
  });
});
