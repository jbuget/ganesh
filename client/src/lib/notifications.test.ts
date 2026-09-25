import { describe, expect, it } from "vitest";

import { notificationSentence } from "@/lib/notifications";
import { NotificationKind } from "@/lib/api/generated/model";
import type { NotificationResponse } from "@/lib/api/generated/model";

const NINO = { id: 2, display_name: "Nino Garo", initials: "NG" };
const SITE = { id: 42, label: "Refonte du site" };

function line(
  kind: NotificationKind,
  over: Partial<NotificationResponse> = {},
): NotificationResponse {
  return {
    id: 1,
    at: "2026-09-17T10:00:00",
    kind,
    actor: NINO,
    project: SITE,
    day: null,
    count: 1,
    read_at: null,
    payload: null,
    ...over,
  };
}

describe("notificationSentence", () => {
  it("names who acted, then what they did", () => {
    const said = notificationSentence(line("project.assigned"));

    expect(said.who).toBe("Nino Garo");
    expect(said.what).toBe("vous a ajouté comme intervenant sur");
    expect(said.about).toBe("Refonte du site");
  });

  it("tells a referent from a contributor", () => {
    const said = notificationSentence(
      line("project.assigned", { payload: { role: "lead" } }),
    );

    expect(said.what).toBe("vous a ajouté comme référent sur");
  });

  it("says a removal in the same terms", () => {
    const said = notificationSentence(
      line("project.unassigned", { payload: { role: "lead" } }),
    );

    expect(said.what).toBe("vous a retiré comme référent de");
  });

  it("reads an edited month by its month, not by its day", () => {
    const said = notificationSentence(
      line("timesheet.edited", { day: "2026-01-01", count: 1 }),
    );

    expect(said.what).toBe("a modifié votre feuille de temps de");
    expect(said.about).toBe("janvier 2026");
  });

  it("counts the repeats of a gesture that folded", () => {
    const said = notificationSentence(
      line("timesheet.edited", { day: "2026-01-01", count: 22 }),
    );

    expect(said.detail).toBe("22 modifications");
  });

  it("says nothing of a count of one", () => {
    const said = notificationSentence(line("timesheet.edited", { day: "2026-01-01" }));

    expect(said.detail).toBeUndefined();
  });

  it("names the two ends of a phase that moved", () => {
    const said = notificationSentence(
      line("project.status_changed", {
        payload: { from: "scoping", to: "development" },
      }),
    );

    expect(said.what).toBe("a fait passer en Réalisation");
    expect(said.about).toBe("Refonte du site");
  });

  it("falls back on the mission carried in the payload once it is gone", () => {
    const said = notificationSentence(
      line("project.deleted", {
        project: null,
        payload: { project_label: "Ancien chantier" },
      }),
    );

    expect(said.what).toBe("a supprimé le projet");
    expect(said.about).toBe("Ancien chantier");
  });

  it("says « Quelqu'un » of an account that has been removed", () => {
    const said = notificationSentence(line("project.assigned", { actor: null }));

    expect(said.who).toBe("Un compte supprimé");
  });

  it("gives every kind a sentence", () => {
    // Read from the generated contract rather than copied out: a kind added
    // server-side reaches this test on its own, and fails it until somebody
    // says it in French.
    const KINDS = Object.values(NotificationKind);

    for (const kind of KINDS) {
      const said = notificationSentence(line(kind, { day: "2026-01-01" }));
      expect(said.what, kind).not.toBe("");
      expect(said.what, kind).toBeTruthy();
    }
  });
});

describe("a need somebody filed", () => {
  it("says what is waiting without having to open it", () => {
    const said = notificationSentence(
      line("request.submitted", {
        project: null,
        request_id: 7,
        payload: { title: "Relances de paiement à la main" },
      }),
    );

    expect(said.what).toBe("a déposé la demande");
    expect(said.about).toBe("Relances de paiement à la main");
    expect(said.href).toBe("/requests?request=7");
  });
});

describe("where a notification leads", () => {
  it("opens the mission it speaks of", () => {
    expect(notificationSentence(line("project.assigned")).href).toBe("/projects/42");
  });

  it("opens the month it speaks of", () => {
    expect(
      notificationSentence(line("timesheet.edited", { day: "2026-01-01" })).href,
    ).toBe("/timesheet?month=2026-01");
  });

  it("opens the thread on the update one was told about", () => {
    expect(
      notificationSentence(
        line("project.update_posted", { payload: { update_id: 412 } }),
      ).href,
    ).toBe("/notifications?mission=42&tab=updates&update=412");
  });

  it("opens the thread of a mention the same way", () => {
    expect(
      notificationSentence(line("update.mention", { payload: { update_id: 412 } }))
        .href,
    ).toBe("/notifications?mission=42&tab=updates&update=412");
  });

  it("opens the thread whole when the update itself is not named", () => {
    expect(notificationSentence(line("project.update_posted")).href).toBe(
      "/notifications?mission=42&tab=updates",
    );
  });

  it("leads nowhere once the mission is gone", () => {
    expect(
      notificationSentence(line("project.deleted", { project: null })).href,
    ).toBeUndefined();
  });
});
