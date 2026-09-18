import { describe, expect, it } from "vitest";

import { depuis } from "./relative-dates";

const MAINTENANT = new Date("2026-09-17T12:00:00");

describe("depuis", () => {
  it("says « à l'instant » within the minute", () => {
    expect(depuis("2026-09-17T11:59:30", MAINTENANT)).toBe("à l'instant");
  });

  it("counts minutes, then hours", () => {
    expect(depuis("2026-09-17T11:20:00", MAINTENANT)).toBe("il y a 40 min");
    expect(depuis("2026-09-17T09:00:00", MAINTENANT)).toBe("il y a 3 h");
  });

  it("says « hier » rather than « il y a 1 j »", () => {
    expect(depuis("2026-09-16T10:00:00", MAINTENANT)).toBe("hier");
  });

  it("counts days up to a week", () => {
    expect(depuis("2026-09-14T12:00:00", MAINTENANT)).toBe("il y a 3 j");
  });

  it("gives the date beyond that, since one gets one's bearings better", () => {
    expect(depuis("2026-08-11T12:00:00", MAINTENANT)).toBe("le 11 août");
  });
});
