import { describe, expect, it } from "vitest";

import { RequestState, type RequestResponse } from "@/lib/api/generated/model";
import type { UserResponse } from "@/lib/api/generated/model";
import { A_WEEK_ON_SITE } from "@/lib/presence";
import {
  REQUEST_STATES,
  mayArbitrate,
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

describe("who may weigh a need", () => {
  const manager: UserResponse = {
    id: 1,
    email: "j.buget@waat.fr",
    display_name: "J. Buget",
    initials: "JB",
    role: "MANAGER",
    is_active: true,
    presence: A_WEEK_ON_SITE,
    reminder_cadence: "DAILY",
  };
  const handed = { ...REQUEST, state: "submitted" as const };

  it("lets a manager weigh what was handed over", () => {
    expect(mayArbitrate(handed, manager)).toBe(true);
  });

  it("turns away everybody else", () => {
    expect(mayArbitrate(handed, { ...manager, role: "TEAMMATE" })).toBe(false);
    expect(mayArbitrate(handed, undefined)).toBe(false);
  });

  it("turns away the manager who asked for it", () => {
    expect(
      mayArbitrate({ ...handed, requester: { id: 1, label: "J. Buget" } }, manager),
    ).toBe(false);
  });

  it("turns away a manager who carries it to the COMEX", () => {
    expect(
      mayArbitrate({ ...handed, sponsors: [{ id: 1, label: "J. Buget" }] }, manager),
    ).toBe(false);
  });

  it("weighs nothing that is still being written, or already built", () => {
    expect(mayArbitrate({ ...handed, state: "draft" }, manager)).toBe(false);
    expect(mayArbitrate({ ...handed, state: "converted" }, manager)).toBe(false);
  });

  it("plays an arbitration again as long as nothing was built", () => {
    expect(mayArbitrate({ ...handed, state: "deferred" }, manager)).toBe(true);
  });
});
