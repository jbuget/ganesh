import { describe, expect, it } from "vitest";

import {
  blocker,
  opensMonth,
  sameScenario,
  scenarioNotice,
  slippage,
  slippageLabel,
  supposesSomething,
} from "./planning";

describe("slippage", () => {
  it("takes the server's word for what is late", () => {
    // The threshold lives on the server: the mark on a row and the tally at
    // the top must never be worked out twice, and differently.
    expect(slippage(9, true)).toBe("late");
  });

  it("reads a landing ahead of the date announced as early", () => {
    expect(slippage(-9, false)).toBe("early");
  });

  it("reads anything else the server forgave as on time", () => {
    expect(slippage(2, false)).toBe("on-time");
  });

  it("says nothing of a mission with no date announced", () => {
    expect(slippage(null, false)).toBe("none");
  });
});

describe("slippageLabel", () => {
  it("counts the days late", () => {
    expect(slippageLabel(5, true)).toBe("5 jours de retard");
  });

  it("counts the days early", () => {
    expect(slippageLabel(-5, false)).toBe("5 jours d'avance");
  });

  it("keeps a single day singular", () => {
    expect(slippageLabel(1, true)).toBe("1 jour de retard");
    expect(slippageLabel(-1, false)).toBe("1 jour d'avance");
  });

  it("says a landing the server forgave is on time", () => {
    expect(slippageLabel(1, false)).toBe("Dans les temps");
  });
});

describe("blocker", () => {
  it("names what to do about it, not just what is wrong", () => {
    expect(blocker("no_estimate")?.hint).toContain("Estimez");
    expect(blocker("no_assignee")?.hint).toContain("Affectez");
  });

  it("says nothing of a mission that could be planned", () => {
    expect(blocker(null)).toBeNull();
  });
});

describe("sameScenario", () => {
  const base = { horizonMonths: 6, order: [10, 20], staffing: { 10: [1, 2] } };

  it("recognises the same hypothesis", () => {
    expect(sameScenario(base, { ...base })).toBe(true);
  });

  it("ignores the order the staffing happens to come in", () => {
    // Clicking Alice then Bob must not read as a different hypothesis from
    // the same pair loaded back the other way round.
    expect(sameScenario(base, { ...base, staffing: { 10: [2, 1] } })).toBe(true);
  });

  it("tells a different queue apart", () => {
    expect(sameScenario(base, { ...base, order: [20, 10] })).toBe(false);
  });

  it("tells a different team apart", () => {
    expect(sameScenario(base, { ...base, staffing: { 10: [1] } })).toBe(false);
  });

  it("counts the horizon as part of the scenario", () => {
    // A scenario kept at six months is not the one kept at twelve.
    expect(sameScenario(base, { ...base, horizonMonths: 12 })).toBe(false);
  });

  it("tells staffing on another mission apart", () => {
    expect(sameScenario(base, { ...base, staffing: { 20: [1, 2] } })).toBe(false);
  });
});

describe("supposesSomething", () => {
  it("an untouched plan supposes nothing", () => {
    expect(supposesSomething({ horizonMonths: 6, order: [], staffing: {} })).toBe(
      false,
    );
  });

  it("a queue makes it a hypothesis", () => {
    expect(supposesSomething({ horizonMonths: 6, order: [10], staffing: {} })).toBe(
      true,
    );
  });

  it("so does putting somebody on a mission", () => {
    expect(
      supposesSomething({ horizonMonths: 6, order: [], staffing: { 10: [] } }),
    ).toBe(true);
  });
});

describe("opensMonth", () => {
  const weeks = ["2026-09-21", "2026-09-28", "2026-10-05"];

  it("the first column always names its month", () => {
    expect(opensMonth(weeks, 0)).toBe(true);
  });

  it("a week inside the same month names nothing", () => {
    expect(opensMonth(weeks, 1)).toBe(false);
  });

  it("the week that opens a month names it", () => {
    expect(opensMonth(weeks, 2)).toBe(true);
  });
});

describe("scenarioNotice", () => {
  it("names the simulation being read", () => {
    expect(scenarioNotice("Priorité bailleurs", false)).toContain(
      "« Priorité bailleurs »",
    );
  });

  it("says when it has drifted from what was saved", () => {
    expect(scenarioNotice("Priorité bailleurs", true)).toContain(
      "modifiée depuis son enregistrement",
    );
  });

  it("says nothing of a drift there is none of", () => {
    expect(scenarioNotice("Priorité bailleurs", false)).not.toContain("modifiée");
  });

  it("says a hypothesis nobody named is not written down", () => {
    expect(scenarioNotice(null, false)).toContain("rien n'est enregistré");
  });

  it("always says the plan changes nothing real", () => {
    // The one thing nobody must misread: a scenario steers no decision.
    expect(scenarioNotice("Piste", false)).toContain("ne change rien au réel");
    expect(scenarioNotice(null, false)).toContain("fiche du projet");
  });
});
