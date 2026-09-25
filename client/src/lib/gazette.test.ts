import { describe, expect, it } from "vitest";

import type {
  ChapterResponse,
  DigestResponse,
  HighlightResponse,
  MovementResponse,
  TallyResponse,
} from "@/lib/api/generated/model";
import {
  chapterKey,
  chapterLine,
  chapterTitle,
  emphasiseProjects,
  highlightSentence,
  isQuietMonth,
  missionName,
  movementPredicate,
  movementSentence,
  projectLabels,
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

function chapter(fields: Partial<ChapterResponse>): ChapterResponse {
  return {
    of: "project",
    project_id: 7,
    label: "Ganesh",
    movements: [],
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
  requests_filed: 0,
  requests_converted: 0,
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

  it("says a return without agreeing with anybody's gender", () => {
    /* « est revenue » for half the team, and the application holds no
       gender — rightly. */
    expect(
      movementSentence(
        movement({ kind: "teammate_returned", subject: "Léa", project_id: null }),
      ),
    ).toBe("Léa est de retour dans l'équipe");
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
    chapters: [],
    highlights: [],
    versions: [],
  } satisfies DigestResponse;

  it("is quiet when the register holds nothing of the month", () => {
    expect(isQuietMonth(digest)).toBe(true);
  });

  it("is not quiet as soon as one mission has a chapter", () => {
    expect(isQuietMonth({ ...digest, chapters: [chapter({})] })).toBe(false);
  });
});

describe("versionLabel", () => {
  it("says which generation, and when it was read", () => {
    expect(versionLabel(2, "2026-10-05T11:30:00")).toMatch(
      /^Version 2 — 5 octobre 2026/,
    );
  });
});

describe("projectLabels", () => {
  const digest = {
    month: "2026-09-01",
    is_generated: true,
    version: 1,
    generated_at: "2026-10-02T09:00:00",
    requested_by: "Léa Chen",
    prose: null,
    prose_model: null,
    tally: NOTHING,
    chapters: [
      chapter({
        label: "Ganesh",
        movements: [movement({ subject: "Lot API", project_id: 9 })],
      }),
      chapter({ project_id: null, label: null }),
    ],
    highlights: [
      highlight({ label: "WAATcher", project_id: 2 }),
      highlight({ kind: "teammate_joined", label: "Sam Okafor", project_id: null }),
    ],
    versions: [],
  } satisfies DigestResponse;

  it("gathers the projects the digest names, its packages counted in", () => {
    expect(projectLabels(digest)).toEqual(["Ganesh", "Lot API", "WAATcher"]);
  });

  it("leaves out the people: only projects are set apart", () => {
    expect(projectLabels(digest)).not.toContain("Sam Okafor");
  });
});

describe("emphasiseProjects", () => {
  it("sets apart a project the prose names", () => {
    expect(emphasiseProjects("Ganesh est passé en exploitation.", ["Ganesh"])).toEqual([
      { text: "Ganesh", isProject: true },
      { text: " est passé en exploitation.", isProject: false },
    ]);
  });

  it("leaves prose naming nothing in one piece", () => {
    expect(emphasiseProjects("Un mois de cadrage.", ["Ganesh"])).toEqual([
      { text: "Un mois de cadrage.", isProject: false },
    ]);
  });

  it("leaves prose alone when the digest names no project", () => {
    expect(emphasiseProjects("Un mois calme.", [])).toEqual([
      { text: "Un mois calme.", isProject: false },
    ]);
  });

  it("sets apart every mention, not only the first", () => {
    const segments = emphasiseProjects("Ganesh avance, et Ganesh livre.", ["Ganesh"]);

    expect(segments.filter((piece) => piece.isProject)).toHaveLength(2);
  });

  it("reads a name whatever case the model gave it", () => {
    const segments = emphasiseProjects(
      "l'Amélioration des algorithmes a été archivée.",
      ["Amélioration des algorithmes"],
    );

    expect(segments[1]).toEqual({
      text: "Amélioration des algorithmes",
      isProject: true,
    });
  });

  it("takes a name carrying regex punctuation literally", () => {
    /* « RAGGAE- AssistantStudio (Usine à "ChatBot") » is a real label. */
    const label = 'RAGGAE- AssistantStudio (Usine à "ChatBot")';

    expect(emphasiseProjects(`Puis ${label}.`, [label])[1]).toEqual({
      text: label,
      isProject: true,
    });
  });

  it("does not let a shorter name steal a longer one", () => {
    const segments = emphasiseProjects("RAGGAE- AssistantStudio avance.", [
      "RAGGAE",
      "RAGGAE- AssistantStudio",
    ]);

    expect(segments[0]).toEqual({
      text: "RAGGAE- AssistantStudio",
      isProject: true,
    });
  });

  it("recognises a name whose label ends in a full stop", () => {
    /* Several labels do, and the model drops it mid-sentence. */
    const segments = emphasiseProjects("Lecture des fichiers tableurs a été archivé.", [
      "Lecture des fichiers tableurs.",
    ]);

    expect(segments[0]).toEqual({
      text: "Lecture des fichiers tableurs",
      isProject: true,
    });
  });

  it("leaves a rearranged name plain rather than guessing", () => {
    /* Emphasis is a claim that this is the project. A claim is not guessed. */
    const segments = emphasiseProjects("le SFTP de WAAT / Suez a été livré.", [
      "WAAT / Suez - SFTP",
    ]);

    expect(segments.some((piece) => piece.isProject)).toBe(false);
  });
});

describe("missionName", () => {
  it("drops the full stop a label was typed with", () => {
    /* Left on, the gazette reads « … dans les PDF. a été archivé ». */
    expect(missionName("Lecture des fichiers tableurs.")).toBe(
      "Lecture des fichiers tableurs",
    );
  });

  it("leaves a name that carries none alone", () => {
    expect(missionName("WAATcher")).toBe("WAATcher");
  });

  it("never empties a name made of nothing else", () => {
    expect(missionName("...")).toBe("...");
  });
});

describe("movementPredicate", () => {
  it("leaves the subject out, for a line read under a heading", () => {
    expect(movementPredicate(movement({ kind: "went_live" }))).toBe(
      "est passé en exploitation",
    );
  });

  it("keeps both ends of a phase that moved", () => {
    expect(
      movementPredicate(
        movement({
          kind: "phase_advanced",
          from_status: "scoping",
          to_status: "development",
        }),
      ),
    ).toBe("est passé de Cadrage à Réalisation");
  });

  it("says a news was posted without turning the sentence round", () => {
    expect(movementPredicate(movement({ kind: "news_posted" }))).toBe(
      "une actualité a été publiée",
    );
  });
});

describe("chapterTitle", () => {
  it("names the mission a chapter is about", () => {
    expect(chapterTitle(chapter({ label: "WAATcher" }))).toBe("WAATcher");
  });

  it("drops the full stop the label was typed with", () => {
    expect(chapterTitle(chapter({ label: "Lecture des tableurs." }))).toBe(
      "Lecture des tableurs",
    );
  });

  it("names in French the chapter that is about no mission", () => {
    expect(chapterTitle(chapter({ project_id: null, label: null }))).toBe("L'équipe");
  });
});

describe("chapterLine", () => {
  const ganesh = chapter({ project_id: 7, label: "Ganesh" });

  it("leaves the project unnamed: its heading says it already", () => {
    expect(
      chapterLine(movement({ kind: "project_archived", project_id: 7 }), ganesh),
    ).toBe("a été archivé");
  });

  it("names the work package, which the heading does not", () => {
    expect(
      chapterLine(
        movement({ kind: "project_archived", subject: "Lot API", project_id: 9 }),
        ganesh,
      ),
    ).toBe("Lot API a été archivé");
  });

  it("names the person in the chapter about no project", () => {
    expect(
      chapterLine(
        movement({ kind: "teammate_joined", subject: "Sam", project_id: null }),
        chapter({ project_id: null, label: null }),
      ),
    ).toBe("Sam a rejoint l'équipe");
  });
});

describe("what the company asked for", () => {
  it("says every fact of a need, agreeing with it", () => {
    // « une demande » is feminine, and nothing but opening the screen would
    // catch a « a été accepté ».
    const said = (kind: MovementResponse["kind"]) =>
      movementPredicate(movement({ kind }));

    expect(said("request_filed")).toBe("a été déposée");
    expect(said("request_accepted")).toBe("a été acceptée");
    expect(said("request_rejected")).toBe("a été refusée");
    expect(said("request_deferred")).toBe("a été reportée à plus tard");
    expect(said("request_converted")).toBe("est devenue un projet");
  });

  it("tells its chapter from the team's, which carries no project either", () => {
    // Keyed on the project alone, the two opened and closed together.
    const needs = chapter({ of: "requests", project_id: null, label: null });
    const team = chapter({ of: "team", project_id: null, label: null });

    expect(chapterKey(needs)).not.toBe(chapterKey(team));
    expect(chapterKey(chapter({ of: "project", project_id: 7 }))).toBe("project:7");
  });

  it("gathers them under a heading of their own", () => {
    // A need is not a mission: the whole feature rests on not confusing them.
    expect(
      chapterTitle(chapter({ of: "requests", project_id: null, label: null })),
    ).toBe("Les demandes");
    expect(chapterTitle(chapter({ of: "team", project_id: null, label: null }))).toBe(
      "L'équipe",
    );
  });

  it("counts what was asked apart from what was built", () => {
    const lines = tallyLines({
      ...NOTHING,
      requests_filed: 6,
      requests_converted: 1,
    });

    expect(lines).toContainEqual({ label: "demandes déposées", value: 6 });
    expect(lines).toContainEqual({ label: "demande devenue un projet", value: 1 });
  });
});
