import { describe, expect, it } from "vitest";

import { auditSentence, groupAuditByDay } from "@/lib/audit-log";
import type { AuditAction, AuditLogEntryResponse } from "@/lib/api/generated/model";

const LIN = { id: 1, display_name: "Lin Chen", initials: "LC" };
const NINO = { id: 2, display_name: "Nino Garo", initials: "NG" };

function entry(
  action: AuditAction,
  over: Partial<AuditLogEntryResponse> = {},
): AuditLogEntryResponse {
  return {
    id: 1,
    at: "2026-09-17T10:00:00",
    action,
    actor: LIN,
    target_user: null,
    day: null,
    field: null,
    old_value: null,
    new_value: null,
    ...over,
  };
}

describe("auditSentence", () => {
  describe("time declared", () => {
    it("reads a day declared for the first time", () => {
      expect(
        auditSentence(
          entry("entry.set", {
            target_user: LIN,
            day: "2026-09-14",
            new_value: "1.0",
          }),
        ),
      ).toEqual({ action: "a déclaré 1 j le 14 sept. 2026" });
    });

    it("spells a half day as the grid does", () => {
      expect(
        auditSentence(
          entry("entry.set", {
            target_user: LIN,
            day: "2026-09-14",
            new_value: "0.5",
          }),
        ).action,
      ).toBe("a déclaré 0,5 j le 14 sept. 2026");
    });

    it("tells a correction from a first declaration", () => {
      expect(
        auditSentence(
          entry("entry.set", {
            target_user: LIN,
            day: "2026-09-14",
            old_value: "0.5",
            new_value: "1.0",
          }),
        ),
      ).toEqual({
        action: "a modifié la déclaration du 14 sept. 2026",
        from: "0,5 j",
        to: "1 j",
      });
    });

    it("names whose month was touched, when it is not one's own", () => {
      expect(
        auditSentence(
          entry("entry.set", {
            target_user: NINO,
            day: "2026-09-14",
            new_value: "1.0",
          }),
        ).action,
      ).toBe("a déclaré 1 j le 14 sept. 2026 pour Nino Garo");
    });

    it("reads a day wiped", () => {
      expect(
        auditSentence(
          entry("entry.clear", {
            target_user: LIN,
            day: "2026-09-14",
            old_value: "0.5",
          }),
        ).action,
      ).toBe("a effacé 0,5 j le 14 sept. 2026");
    });
  });

  describe("the mission's own life", () => {
    it("reads a mission opened", () => {
      expect(auditSentence(entry("project.create")).action).toBe("a créé la mission");
    });

    it("reads a phase moved, both ends in French", () => {
      expect(
        auditSentence(
          entry("project.status_change", {
            old_value: "scoping",
            new_value: "development",
          }),
        ),
      ).toEqual({
        action: "a changé la phase",
        from: "Cadrage",
        to: "Réalisation",
      });
    });

    it("reads a renaming as a renaming", () => {
      expect(
        auditSentence(
          entry("project.update", {
            field: "label",
            old_value: "EDIT",
            new_value: "EDIT v2",
          }),
        ),
      ).toEqual({ action: "a renommé la mission", from: "EDIT", to: "EDIT v2" });
    });

    it("reads an exit from the reference list as an archiving", () => {
      expect(
        auditSentence(
          entry("project.update", {
            field: "is_active",
            old_value: "True",
            new_value: "False",
          }),
        ),
      ).toEqual({ action: "a archivé la mission" });
    });

    it("reads a return as an unarchiving", () => {
      expect(
        auditSentence(
          entry("project.update", {
            field: "is_active",
            old_value: "False",
            new_value: "True",
          }),
        ),
      ).toEqual({ action: "a désarchivé la mission" });
    });

    it("reads a mission joining a project, without naming an id nobody reads", () => {
      expect(
        auditSentence(
          entry("project.update", {
            field: "parent_id",
            old_value: null,
            new_value: "10",
          }),
        ),
      ).toEqual({ action: "a rattaché la mission à un projet" });
    });

    it("reads a work package taken back out", () => {
      expect(
        auditSentence(
          entry("project.update", {
            field: "parent_id",
            old_value: "10",
            new_value: null,
          }),
        ),
      ).toEqual({ action: "a détaché la mission de son projet" });
    });

    it("names the axis on both sides", () => {
      expect(
        auditSentence(
          entry("project.update", {
            field: "category",
            old_value: null,
            new_value: "sustain_growth",
          }),
        ),
      ).toEqual({
        action: "a modifié l'axe stratégique",
        from: "—",
        to: "Pérenniser la croissance",
      });
    });

    it("spells an estimate in days", () => {
      expect(
        auditSentence(
          entry("project.update", {
            field: "estimated_days",
            old_value: "10.0",
            new_value: "12.5",
          }),
        ),
      ).toEqual({ action: "a modifié la charge estimée", from: "10 j", to: "12,5 j" });
    });

    it("names the departments in French, one by one", () => {
      expect(
        auditSentence(
          entry("project.update", {
            field: "departments",
            old_value: "landlords",
            new_value: "condominium, landlords",
          }),
        ),
      ).toEqual({
        action: "a modifié les pôles concernés",
        from: "Bailleurs",
        to: "Copropriété, Bailleurs",
      });
    });

    it("says a sheet was published rather than a flag flipped", () => {
      expect(
        auditSentence(
          entry("project.update", {
            field: "is_published",
            old_value: "False",
            new_value: "True",
          }),
        ),
      ).toEqual({ action: "a publié la fiche service" });
    });

    it("keeps a long text out of the line and only says it moved", () => {
      expect(auditSentence(entry("project.update", { field: "description" }))).toEqual({
        action: "a modifié la fiche détaillée",
      });
    });

    it("falls back on the field's own name rather than saying nothing", () => {
      expect(
        auditSentence(entry("project.update", { field: "unheard_of", new_value: "x" }))
          .action,
      ).toBe("a modifié unheard_of");
    });
  });

  describe("who works on it", () => {
    it("reads a contributor declared", () => {
      expect(
        auditSentence(
          entry("project.assign", { target_user: NINO, new_value: "contributor" }),
        ),
      ).toEqual({ action: "a ajouté Nino Garo aux intervenants" });
    });

    it("tells a lead from a contributor", () => {
      expect(
        auditSentence(entry("project.assign", { target_user: NINO, new_value: "lead" }))
          .action,
      ).toBe("a ajouté Nino Garo comme référent");
    });

    it("reads a contributor taken off", () => {
      expect(
        auditSentence(
          entry("project.unassign", { target_user: NINO, old_value: "contributor" }),
        ).action,
      ).toBe("a retiré Nino Garo des intervenants");
    });
  });

  describe("the follow-up thread", () => {
    it("reads a message posted", () => {
      expect(auditSentence(entry("update.post")).action).toBe(
        "a publié une mise à jour",
      );
    });

    it("reads a message withdrawn", () => {
      expect(auditSentence(entry("update.remove")).action).toBe(
        "a supprimé une mise à jour",
      );
    });
  });

  it("says something rather than nothing for an action it does not know", () => {
    expect(auditSentence(entry("user.role_change")).action).toBe(
      "a effectué une action",
    );
  });
});

describe("groupAuditByDay", () => {
  function on(at: string): AuditLogEntryResponse {
    return { ...entry("project.update"), at };
  }

  it("says the day once, over the gestures made that day", () => {
    const days = groupAuditByDay([
      on("2026-09-17T14:05:00"),
      on("2026-09-17T09:12:00"),
      on("2026-09-16T18:00:00"),
    ]);

    expect(days.map((one) => one.day)).toEqual(["2026-09-17", "2026-09-16"]);
    expect(days[0].entries).toHaveLength(2);
  });

  it("keeps the order it was served in, so pages stack", () => {
    const days = groupAuditByDay([
      on("2026-09-16T18:00:00"),
      on("2026-09-17T09:12:00"),
    ]);

    expect(days.map((one) => one.day)).toEqual(["2026-09-16", "2026-09-17"]);
  });

  it("has no day to show for an empty log", () => {
    expect(groupAuditByDay([])).toEqual([]);
  });
});
