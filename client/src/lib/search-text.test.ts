import { describe, expect, it } from "vitest";

import { normalise } from "./search-text";

describe("normalise", () => {
  it("drops the case", () => {
    expect(normalise("Portail Bailleurs")).toBe("portail bailleurs");
  });

  it("drops the accents, so that « copropriete » finds « copropriété »", () => {
    expect(normalise("Copropriété")).toBe("copropriete");
    expect(normalise("Jérémy")).toBe("jeremy");
  });

  it("leaves the rest of the text alone", () => {
    expect(normalise("API / MCP")).toBe("api / mcp");
  });
});
