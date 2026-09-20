import { describe, expect, it } from "vitest";

import type {
  DigestResponse,
  HighlightResponse,
  MovementResponse,
  TallyResponse,
} from "@/lib/api/generated/model";
import {
  highlightSentence,
  isQuietMonth,
  movementSentence,
  tallyLines,
  versionLabel,
} from "@/lib/gazette";

function movement(fields: Partial<MovementResponse>): MovementResponse {
  return {
    kind: "project_created",
    at: "2026-09-04T10:00:00",
    subject: "Ganesh",
    project_id: 7,
    from_status: null,
    to_status: null,
    ...fields,
  };
}

function highlight(fields: Partial<HighlightResponse>): HighlightResponse {
  return {
    kind: "went_live",
    tone: "notable",
    project_id: 7,
    label: "WAATcher",
    ...fields,
  };
}

const NOTHING: TallyResponse = {
  projects_created: 0,
  projects_archived: 0,
  phase_changes: 0,
  news_posted: 0,
  months_validated: 0,
};

describe("movementSentence", () => {
  it("names a project that joined the reference list", () => {
    expect(movementSentence(movement({ kind: "project_created" }))).toBe(
      "Ganesh a rejoint la liste des projets",
    );
  });

  it("says « projet », never « mission »", () => {
    const sentences = (["project_created", "project_revived"] as const).map((kind) =>
      movementSentence(movement({ kind })),
    );

    expect(sentences.join(" ")).not.toMatch(/mission/i);
  });

  it("agrees in the masculine, as « projet » does", () => {
    expect(movementSentence(movement({ kind: "project_archived" }))).toBe(
      "Ganesh a été archivé",
    );
  });

  it("reads a phase that moved on, both ends named", () => {
    expect(
      movementSentence(
        movement({
          kind: "phase_advanced",
          from_status: "scoping",
          to_status: "development",
        }),
      ),
    ).toBe("Ganesh est passé de Cadrage à Réalisation");
  });

  it("reads a phase that went back", () => {
    expect(
      movementSentence(
        movement({
          kind: "phase_stepped_back",
          subject: "NOMAD",
          from_status: "validation",
          to_status: "development",
        }),
      ),
    ).toBe("NOMAD est revenu de Validation à Réalisation");
  });

  it("elides before a phase that opens on a vowel", () => {
    expect(
      movementSentence(
        movement({
          kind: "phase_stepped_back",
          from_status: "operations",
          to_status: "deployment",
        }),
      ),
    ).toBe("Ganesh est revenu d'Exploitation à Déploiement");
  });

  it("names only the phase the register recorded", () => {
    expect(
      movementSentence(
        movement({ kind: "phase_advanced", from_status: null, to_status: "scoping" }),
      ),
    ).toBe("Ganesh est passé en Cadrage");
  });

  it("tells a mise en service apart from any other phase move", () => {
    expect(
      movementSentence(
        movement({ kind: "went_live", subject: "WAATcher", to_status: "operations" }),
      ),
    ).toBe("WAATcher est passé en exploitation");
  });

  it("puts the project after the action when the news is the subject", () => {
    expect(movementSentence(movement({ kind: "news_posted" }))).toBe(
      "Une actualité a été publiée sur Ganesh",
    );
  });

  it("names who joined and who left", () => {
    expect(
      movementSentence(movement({ kind: "teammate_joined", subject: "Sam" })),
    ).toBe("Sam a rejoint l'équipe");
    expect(movementSentence(movement({ kind: "teammate_left", subject: "Léa" }))).toBe(
      "Léa a quitté l'équipe",
    );
  });
});

describe("highlightSentence", () => {
  it("reads a mise en service", () => {
    expect(highlightSentence(highlight({ kind: "went_live" }))).toBe(
      "WAATcher est passé en exploitation",
    );
  });

  it("reads a mission given up on before it ever ran", () => {
    expect(highlightSentence(highlight({ kind: "archived_before_delivery" }))).toBe(
      "WAATcher a été archivé sans avoir été mis en service",
    );
  });

  it("reads an announced date that went by", () => {
    expect(highlightSentence(highlight({ kind: "go_live_overdue" }))).toBe(
      "WAATcher a dépassé sa date de mise en service annoncée",
    );
  });

  it("names a mission and never a person", () => {
    const sentences = (
      [
        "went_live",
        "phase_stepped_back",
        "archived_before_delivery",
        "go_live_overdue",
      ] as const
    ).map((kind) => highlightSentence(highlight({ kind })));

    expect(sentences.every((sentence) => sentence.startsWith("WAATcher"))).toBe(true);
  });
});

describe("tallyLines", () => {
  it("agrees with the figure it sits beside", () => {
    const lines = tallyLines({ ...NOTHING, projects_created: 1 });

    expect(lines[0]).toEqual({ label: "projet créé", value: 1 });
  });

  it("agrees in the plural past one", () => {
    const lines = tallyLines({ ...NOTHING, projects_created: 4 });

    expect(lines[0]).toEqual({ label: "projets créés", value: 4 });
  });

  it("reads a figure of zero in the singular", () => {
    expect(tallyLines(NOTHING)[3].label).toBe("actualité publiée");
  });

  it("agrees in the feminine where the word is", () => {
    const lines = tallyLines({ ...NOTHING, news_posted: 3 });

    expect(lines[3]).toEqual({ label: "actualités publiées", value: 3 });
  });

  it("counts the months closed without naming anyone", () => {
    const lines = tallyLines({ ...NOTHING, months_validated: 9 });

    expect(lines[4]).toEqual({ label: "mois validés", value: 9 });
  });
});

describe("isQuietMonth", () => {
  const digest = {
    month: "2026-09-01",
    is_generated: false,
    version: null,
    generated_at: null,
    requested_by: null,
    prose: null,
    prose_model: null,
    tally: NOTHING,
    movements: [],
    highlights: [],
    versions: [],
  } satisfies DigestResponse;

  it("is quiet when the register holds nothing of the month", () => {
    expect(isQuietMonth(digest)).toBe(true);
  });

  it("is not quiet as soon as one fact was recorded", () => {
    expect(isQuietMonth({ ...digest, movements: [movement({})] })).toBe(false);
  });
});

describe("versionLabel", () => {
  it("says which generation, and when it was read", () => {
    expect(versionLabel(2, "2026-10-05T11:30:00")).toMatch(
      /^Version 2 — 5 octobre 2026/,
    );
  });
});
