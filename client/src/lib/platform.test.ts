import { describe, expect, it } from "vitest";

import { doorDetail, doorLabel, serviceLabel, serviceSays } from "@/lib/platform";

describe("doorLabel", () => {
  it("names each door in French", () => {
    expect(doorLabel("ENTRA")).toBe("Microsoft Entra ID");
    expect(doorLabel("LOCAL")).toBe("Porte de secours");
    expect(doorLabel("OPEN")).toBe("Aucune");
  });

  it("says out loud what no door at all means", () => {
    expect(doorDetail("OPEN")).toMatch(/jamais laisser en production/);
  });
});

describe("serviceSays", () => {
  it("names the address of a service that is wired", () => {
    expect(
      serviceSays({ name: "smtp", configured: true, detail: "smtp.mailgun.org:587" }),
    ).toBe("smtp.mailgun.org:587");
  });

  it("says what a missing service costs rather than calling it a fault", () => {
    // Two of the four are optional by design: « non câblé » on its own would
    // read as something broken.
    expect(serviceSays({ name: "gemini", configured: false, detail: "" })).toMatch(
      /sans chapeau/,
    );
    expect(serviceSays({ name: "smtp", configured: false, detail: "" })).toMatch(
      /Aucune lettre/,
    );
  });

  it("falls back rather than showing a name nobody wrote a line for", () => {
    expect(serviceLabel("kafka")).toBe("kafka");
    expect(serviceSays({ name: "kafka", configured: false, detail: "" })).toBe(
      "Non câblé.",
    );
  });
});
