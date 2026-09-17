import { describe, expect, it } from "vitest";

import { depuis } from "./dates-relatives";

const MAINTENANT = new Date("2026-09-17T12:00:00");

describe("depuis", () => {
  it("dit « à l'instant » dans la minute", () => {
    expect(depuis("2026-09-17T11:59:30", MAINTENANT)).toBe("à l'instant");
  });

  it("compte les minutes, puis les heures", () => {
    expect(depuis("2026-09-17T11:20:00", MAINTENANT)).toBe("il y a 40 min");
    expect(depuis("2026-09-17T09:00:00", MAINTENANT)).toBe("il y a 3 h");
  });

  it("dit « hier » plutôt que « il y a 1 j »", () => {
    expect(depuis("2026-09-16T10:00:00", MAINTENANT)).toBe("hier");
  });

  it("compte les jours jusqu'à une semaine", () => {
    expect(depuis("2026-09-14T12:00:00", MAINTENANT)).toBe("il y a 3 j");
  });

  it("donne la date au-delà, car on s'y repère mieux", () => {
    expect(depuis("2026-08-11T12:00:00", MAINTENANT)).toBe("le 11 août");
  });
});
