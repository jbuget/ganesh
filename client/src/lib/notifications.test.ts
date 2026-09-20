import { describe, expect, it } from "vitest";

import { notificationSentence } from "@/lib/notifications";
import type { NotificationKind, NotificationResponse } from "@/lib/api/generated/model";

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
      line("project.assigned", { payload: { role: "referent" } }),
    );

    expect(said.what).toBe("vous a ajouté comme référent sur");
  });

  it("says a removal in the same terms", () => {
    const said = notificationSentence(
      line("project.unassigned", { payload: { role: "referent" } }),
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
    const KINDS: NotificationKind[] = [
      "project.assigned",
      "project.unassigned",
      "timesheet.edited",
      "month.reopened",
      "project.update_posted",
      "project.status_changed",
      "project.archived",
      "project.deleted",
      "user.role_changed",
      "user.deactivated",
      "user.activated",
      "api_key.created",
      "api_key.revoked",
      "update.mention",
    ];

    for (const kind of KINDS) {
      const said = notificationSentence(line(kind, { day: "2026-01-01" }));
      expect(said.what, kind).not.toBe("");
      expect(said.what, kind).toBeTruthy();
    }
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

  it("leads nowhere once the mission is gone", () => {
    expect(
      notificationSentence(line("project.deleted", { project: null })).href,
    ).toBeUndefined();
  });
});
