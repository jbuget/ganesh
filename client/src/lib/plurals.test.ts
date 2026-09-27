import { describe, expect, it } from "vitest";

import { plural, s } from "@/lib/plurals";

describe("plural", () => {
  it("agrees from two on, as French does", () => {
    expect(plural(0, "projet")).toBe("projet");
    expect(plural(1, "projet")).toBe("projet");
    expect(plural(2, "projet")).toBe("projets");
  });
});

describe("s", () => {
  it("carries the agreement a word does not", () => {
    expect(`${0} livré${s(0)}`).toBe("0 livré");
    expect(`${1} livré${s(1)}`).toBe("1 livré");
    expect(`${3} livré${s(3)}`).toBe("3 livrés");
  });
});
