import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api/fetcher";
import {
  MAX_TAGS_PER_PROJECT,
  proposesCreating,
  tagFailureSaid,
  tagNamesAlike,
  visibleTags,
} from "./tags";

const found = (...names: string[]) =>
  names.map((name, index) => ({
    id: index + 1,
    name,
    color: "blue" as const,
    project_count: 1,
  }));

describe("tagNamesAlike", () => {
  it("reads two names that differ by case as one", () => {
    expect(tagNamesAlike("IA", "ia")).toBe(true);
  });

  it("reads two names that differ by accents as one", () => {
    expect(tagNamesAlike("France Énergie 2030", "france energie 2030")).toBe(true);
  });

  it("reads a hyphen, an underscore and a space as the same separator", () => {
    expect(tagNamesAlike("Suez-Env", "suez env")).toBe(true);
    expect(tagNamesAlike("Suez_Env", "Suez   Env")).toBe(true);
  });

  it("tells two different names apart", () => {
    expect(tagNamesAlike("Suez", "Suez Env")).toBe(false);
  });
});

describe("proposesCreating", () => {
  it("proposes to open a tag nobody has opened", () => {
    expect(proposesCreating("Frigo", found("Chronopost"))).toBe(true);
  });

  it("does not propose a tag that already says the same", () => {
    expect(proposesCreating("chronopost", found("Chronopost"))).toBe(false);
  });

  it("proposes nothing while nothing is typed", () => {
    expect(proposesCreating("   ", found())).toBe(false);
  });

  it("still proposes when only a longer tag contains what was typed", () => {
    expect(proposesCreating("Suez", found("Suez Env"))).toBe(true);
  });
});

describe("tagFailureSaid", () => {
  it("says the bound when a project already carries the most it can", () => {
    expect(tagFailureSaid(new ApiError(422, "A mission carries 8 tags at most."))).toBe(
      `Un projet porte ${MAX_TAGS_PER_PROJECT} tags au plus.`,
    );
  });

  it("says a name already taken, and what to do about it", () => {
    expect(tagFailureSaid(new ApiError(409, "A tag already says « Suez »."))).toBe(
      "Un tag porte déjà ce nom : fusionnez-les plutôt.",
    );
  });

  it("says a refusal it cannot tell apart without repeating the server's English", () => {
    expect(tagFailureSaid(new ApiError(422, "A tag needs a name."))).toBe(
      "Ce tag n'a pas pu être enregistré.",
    );
  });

  it("says the same for something that is not an API error at all", () => {
    expect(tagFailureSaid(new Error("boom"))).toBe(
      "Ce tag n'a pas pu être enregistré.",
    );
  });
});

describe("visibleTags", () => {
  const tags = (...names: string[]) =>
    names.map((name, index) => ({ id: index + 1, name, color: "blue" as const }));

  it("shows every tag while they fit", () => {
    const { shown, hidden } = visibleTags(tags("IA", "Suez"), 3);

    expect(shown.map((tag) => tag.name)).toEqual(["IA", "Suez"]);
    expect(hidden).toEqual([]);
  });

  it("keeps the first ones and counts the rest, in the order they come", () => {
    const { shown, hidden } = visibleTags(tags("A", "B", "C", "D"), 2);

    expect(shown.map((tag) => tag.name)).toEqual(["A", "B"]);
    expect(hidden.map((tag) => tag.name)).toEqual(["C", "D"]);
  });

  it("reads a mission with no list of tags as one carrying none", () => {
    expect(visibleTags(undefined, 3)).toEqual({ shown: [], hidden: [] });
  });
});
