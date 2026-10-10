import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { GazettePage } from "./GazettePage";
import type { ChapterResponse, DigestResponse } from "@/lib/api/generated/model";

const gazette = vi.hoisted(() => ({
  cursor: { year: 2026, month: 9 },
  digest: undefined as DigestResponse | undefined,
  isLoading: false,
  isGenerating: false,
  referenceLabels: [] as string[],
  refusal: null as string | null,
  goToPreviousMonth: vi.fn(),
  goToNextMonth: vi.fn(),
  openVersion: vi.fn(),
  generateDigest: vi.fn(),
}));

vi.mock("@/lib/use-gazette", () => ({ useGazette: () => gazette }));
vi.mock("@/components/organisms/SharePanel", () => ({
  SharePanel: ({ version }: { version: number }) => (
    <button type="button">Partager la version {version}</button>
  ),
}));

function aDigest(over: Partial<DigestResponse> = {}): DigestResponse {
  return {
    month: "2026-09-01",
    is_generated: true,
    version: 1,
    generated_at: "2026-10-02T09:30:00",
    requested_by: "Léa Chen",
    prose: "Un mois de cadrage.",
    prose_model: "gemini-2.5-flash",
    spotlights: [],
    tally: {
      projects_created: 2,
      projects_archived: 0,
      phase_changes: 3,
      news_posted: 0,
      months_validated: 9,
      requests_filed: 0,
      requests_converted: 0,
    },
    chapters: [
      {
        of: "project",
        project_id: 2,
        label: "WAATcher",
        movements: [
          {
            kind: "went_live",
            at: "2026-09-12T14:00:00",
            subject: "WAATcher",
            project_id: 2,
            from_status: "deployment",
            to_status: "operations",
          },
        ],
      },
    ] satisfies ChapterResponse[],
    highlights: [
      { kind: "went_live", tone: "notable", project_id: 2, label: "WAATcher" },
      {
        kind: "go_live_overdue",
        tone: "attention",
        project_id: 4,
        label: "SALSA",
      },
    ],
    versions: [
      { version: 1, generated_at: "2026-10-02T09:30:00", requested_by: "Léa Chen" },
    ],
    ...over,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  gazette.digest = aDigest();
  gazette.isGenerating = false;
  gazette.isLoading = false;
  gazette.referenceLabels = [];
  gazette.refusal = null;
});

describe("GazettePage", () => {
  it("offers to share the version on screen", () => {
    render(<GazettePage />);

    expect(screen.getByRole("button", { name: "Partager la version 1" })).toBeVisible();
  });

  it("offers nothing to share on a month nobody has generated", () => {
    gazette.digest = aDigest({ is_generated: false, version: null });

    render(<GazettePage />);

    expect(screen.queryByRole("button", { name: /Partager/ })).toBeNull();
  });

  it("names the month it is reading", () => {
    render(<GazettePage />);

    expect(screen.getByRole("heading", { name: /septembre 2026/i })).toBeVisible();
  });

  it("says who asked for the version on screen, and when", () => {
    render(<GazettePage />);

    expect(screen.getByText(/Version 1, demandée par Léa Chen/)).toBeVisible();
  });

  it("tells the reader the editorial was written by a machine", () => {
    render(<GazettePage />);

    expect(screen.getByText("Un mois de cadrage.")).toBeVisible();
    expect(screen.getByText(/rédigé par gemini-2.5-flash/)).toBeVisible();
  });

  it("sets the projects it names apart in the editorial", () => {
    /* A paragraph of prose is skimmed for what it is about. */
    gazette.digest = aDigest({
      prose: "WAATcher est passé en exploitation, et SALSA est en retard.",
    });

    render(<GazettePage />);

    const emphasised = document.querySelectorAll("strong");
    expect([...emphasised].map((node) => node.textContent)).toEqual([
      "WAATcher",
      "SALSA",
    ]);
  });

  it("tells the editorial in as many paragraphs as the model wrote", () => {
    gazette.digest = aDigest({ prose: "Premier temps.\n\nSecond temps." });

    render(<GazettePage />);

    expect(screen.getByText("Premier temps.")).toBeVisible();
    expect(screen.getByText("Second temps.")).toBeVisible();
  });

  it("puts the projects of the month under the spotlight, with their figures", () => {
    gazette.digest = aDigest({
      spotlights: [
        {
          project_id: 2,
          label: "WAATcher",
          text: "Un outil de suivi des services.\n\nIl est entré en exploitation.",
          status: "operations",
          went_live: true,
          updates_posted: 12,
          days_declared: 18.5,
          contributors: 4,
        },
      ],
    });

    render(<GazettePage />);

    expect(screen.getByRole("heading", { name: "Sous le projecteur" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "WAATcher" })).toBeVisible();
    expect(
      screen.getByText(
        "Mis en service ce mois-ci · 12 mises à jour · 18,5 jours déclarés · 4 personnes",
      ),
    ).toBeVisible();
    expect(screen.getByText("Un outil de suivi des services.")).toBeVisible();
    expect(screen.getByText("Il est entré en exploitation.")).toBeVisible();
  });

  it("tells the editorial and the spotlights in one frame, under one signature", () => {
    gazette.digest = aDigest({
      spotlights: [
        {
          project_id: 2,
          label: "WAATcher",
          text: "Un outil de suivi.",
          status: "operations",
          went_live: false,
          updates_posted: 1,
          days_declared: 0,
          contributors: 0,
        },
      ],
    });

    render(<GazettePage />);

    const frame = screen.getByText("Un mois de cadrage.").closest("section");
    expect(frame).toContainElement(screen.getByText("Sous le projecteur"));
    expect(screen.getAllByText(/rédigé par gemini/)).toHaveLength(1);
  });

  it("sets every name in bold, including a project the digest has no chapter for", () => {
    gazette.referenceLabels = ["NOMAD - Formulaire en ligne"];
    gazette.digest = aDigest({
      prose: "WAATcher avance, et NOMAD recule.",
    });

    render(<GazettePage />);

    const bold = [...document.querySelectorAll("strong")].map((n) => n.textContent);
    expect(bold).toEqual(["WAATcher", "NOMAD"]);
  });

  it("says why a digest could not be generated", () => {
    gazette.refusal =
      "Quelqu'un vient de générer un digest de ce mois. Voici sa version.";

    render(<GazettePage />);

    expect(screen.getByRole("alert")).toHaveTextContent(/Quelqu'un vient de générer/);
  });

  it("shows no spotlight when the model told none", () => {
    render(<GazettePage />);

    expect(screen.queryByText("Sous le projecteur")).toBeNull();
  });

  it("says where the figures come from, beside the paragraph", () => {
    /* The whole screen rests on the reader telling the two apart. */
    render(<GazettePage />);

    expect(screen.getByText(/chiffres, eux, viennent du journal/)).toBeVisible();
  });

  it("holds the facts without a editorial when none was written", () => {
    gazette.digest = aDigest({ prose: null, prose_model: null });

    render(<GazettePage />);

    expect(screen.queryByText(/rédigé par/)).toBeNull();
    expect(screen.getByText(/WAATcher est passé en exploitation/)).toBeVisible();
    expect(screen.getByRole("button", { name: /WAATcher/ })).toBeVisible();
  });

  it("reads the facts in French, never in the register's words", () => {
    render(<GazettePage />);

    expect(
      screen.getByText(/SALSA a dépassé sa date de mise en service/),
    ).toBeVisible();
    expect(screen.queryByText(/go_live_overdue/)).toBeNull();
  });

  it("offers to generate a month nobody has asked for", () => {
    gazette.digest = aDigest({
      is_generated: false,
      version: null,
      generated_at: null,
      requested_by: null,
      prose: null,
      prose_model: null,
      versions: [],
    });

    render(<GazettePage />);

    expect(screen.getByRole("button", { name: "Générer le digest" })).toBeVisible();
    expect(screen.getByText(/pas encore de digest/)).toBeVisible();
  });

  it("asks nothing before a first generation", async () => {
    gazette.digest = aDigest({ is_generated: false, version: null, versions: [] });
    render(<GazettePage />);

    await userEvent.click(screen.getByRole("button", { name: "Générer le digest" }));

    expect(gazette.generateDigest).toHaveBeenCalledTimes(1);
  });

  it("confirms before writing a version over the one being read", async () => {
    render(<GazettePage />);

    await userEvent.click(screen.getByRole("button", { name: "Regénérer" }));

    expect(gazette.generateDigest).not.toHaveBeenCalled();
    expect(screen.getByText(/Regénérer le digest de septembre 2026/)).toBeVisible();
    expect(screen.getByText(/reste consultable/)).toBeVisible();
  });

  it("generates once the reader has confirmed", async () => {
    render(<GazettePage />);
    await userEvent.click(screen.getByRole("button", { name: "Regénérer" }));

    // The dialog carries its own « Regénérer »: the one being confirmed.
    const dialog = screen.getByRole("alertdialog");
    await userEvent.click(within(dialog).getByRole("button", { name: "Regénérer" }));

    expect(gazette.generateDigest).toHaveBeenCalledTimes(1);
  });

  it("keeps every chronicle closed until it is asked for", async () => {
    /* A month of tidying-up touches a dozen projects; a dozen chronicles
       unfolded bury the two that had something to say. */
    render(<GazettePage />);

    expect(screen.queryByText("est passé en exploitation")).toBeNull();

    await userEvent.click(screen.getByRole("button", { name: /WAATcher/ }));

    expect(screen.getByText("est passé en exploitation")).toBeVisible();
  });

  it("says how much happened to a project before it is opened", () => {
    render(<GazettePage />);

    expect(screen.getByRole("button", { name: /WAATcher/ })).toHaveTextContent("1");
  });

  it("names each project once, over its own chronicle", async () => {
    /* « WAATcher est passé en exploitation » under a heading reading
       « WAATcher » says it twice. */
    render(<GazettePage />);

    await userEvent.click(screen.getByRole("button", { name: /WAATcher/ }));

    expect(screen.getByText("est passé en exploitation")).toBeVisible();
  });

  it("names a work package on its line, inside its project", async () => {
    gazette.digest = aDigest({
      chapters: [
        {
          of: "project",
          project_id: 2,
          label: "WAATcher",
          movements: [
            {
              kind: "project_archived",
              at: "2026-09-20T09:00:00",
              subject: "Lot API",
              project_id: 9,
              from_status: null,
              to_status: null,
            },
          ],
        },
      ],
    });
    render(<GazettePage />);

    await userEvent.click(screen.getByRole("button", { name: /WAATcher/ }));

    expect(screen.getByText("Lot API a été archivé")).toBeVisible();
  });

  it("drops the full stop a project name was typed with", () => {
    gazette.digest = aDigest({
      chapters: [
        {
          of: "project",
          project_id: 3,
          label: "Lecture des fichiers tableurs.",
          movements: [],
        },
      ],
    });

    render(<GazettePage />);

    const opener = screen.getByRole("button", { name: /Lecture des fichiers/ });
    expect(opener).toHaveTextContent("Lecture des fichiers tableurs");
    expect(opener.textContent).not.toContain("tableurs.");
  });

  it("says plainly when a month left nothing behind", () => {
    gazette.digest = aDigest({ chapters: [], highlights: [] });

    render(<GazettePage />);

    expect(screen.getByText("Rien n'a été enregistré ce mois-ci.")).toBeVisible();
  });
});
