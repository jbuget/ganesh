import { describe, expect, it } from "vitest";

import { RequestState, type RequestResponse } from "@/lib/api/generated/model";
import {
  REQUEST_STATES,
  missingBeforeSubmitting,
  requestStateLabel,
  sayMissing,
} from "@/lib/requests";

const REQUEST: RequestResponse = {
  id: 1,
  title: "Relances de paiement à la main",
  state: "draft",
  requester: { id: 7, label: "Anne Métier" },
  sponsors: [{ id: 3, label: "C. Direction" }],
  departments: ["finance_admin"],
  created_at: "2026-09-22T10:00:00Z",
};

describe("requestStateLabel", () => {
  it("names every state in French", () => {
    // Read from the generated contract: a state added server-side reaches
    // this test on its own, and fails it until somebody names it.
    for (const state of Object.values(RequestState)) {
      expect(requestStateLabel(state), state).not.toBe(state);
    }
  });

  it("says « Plus tard » rather than « Différée »", () => {
    // Neither a yes nor a no: the label says what was decided, not a status.
    expect(requestStateLabel("deferred")).toBe("Plus tard");
  });

  it("gives every state a dot of its own", () => {
    const dots = new Set(REQUEST_STATES.map((state) => state.dot));

    expect(dots.size).toBe(REQUEST_STATES.length);
  });
});

describe("what is missing before handing a need over", () => {
  it("names the three the API asks for", () => {
    expect(missingBeforeSubmitting(REQUEST)).toEqual([
      "le problème",
      "qui est concerné",
      "le résultat attendu",
    ]);
  });

  it("reads a field of spaces as unsaid", () => {
    expect(missingBeforeSubmitting({ ...REQUEST, problem: "   " })).toContain(
      "le problème",
    );
  });

  it("asks for nothing once the sheet says enough", () => {
    expect(
      missingBeforeSubmitting({
        ...REQUEST,
        problem: "Tapées une par une.",
        impact: "Trois personnes.",
        expected_outcome: "Une relance automatique.",
      }),
    ).toEqual([]);
  });

  it("joins what is missing into a sentence", () => {
    expect(sayMissing(["le problème", "qui est concerné"])).toBe(
      "le problème et qui est concerné",
    );
    expect(sayMissing(["le problème"])).toBe("le problème");
  });
});
