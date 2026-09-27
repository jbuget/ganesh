import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReviewAgendaPage } from "./ReviewAgendaPage";
import type { FlaggedUpdateResponse } from "@/lib/api/generated/model";
import type { AgendaChapter } from "@/lib/review-agenda";

// The total is its own pure function, with its own tests: here it is given,
// so that what is under test stays what the file says it is.
const agenda = vi.hoisted(() => ({
  chapters: null as AgendaChapter[] | null,
  waiting: 0,
  clear: vi.fn(),
}));
vi.mock("@/lib/use-review-agenda", () => ({ useReviewAgenda: () => agenda }));

// Whether this reader may write is its own hook and its own tests.
const mayWrite = vi.hoisted(() => ({ value: true }));
vi.mock("@/lib/use-may-write", () => ({ useMayWrite: () => mayWrite.value }));

vi.mock("@/lib/api/queries", () => ({ useTeammates: () => ({ teammates: [] }) }));

// The panel is its own organism, with its own tests: here only the gesture
// that opens it is under test.
const panel = vi.hoisted(() => ({
  openedMission: null as number | null,
  openTab: null,
  aimedAt: null,
  open: vi.fn(),
  close: vi.fn(),
}));
vi.mock("@/lib/opened-mission", () => ({ useOpenedMission: () => panel }));

function raised(over: Partial<FlaggedUpdateResponse> = {}): FlaggedUpdateResponse {
  return {
    update_id: 1,
    project_id: 10,
    project_label: "Portail",
    body: "Le sponsor attend une date.",
    author: { id: 7, display_name: "L. Chen", initials: "LC" },
    published_at: "2026-09-21T09:00:00Z",
    raised_by: { id: 8, display_name: "N. Garo", initials: "NG" },
    flagged_at: "2026-09-22T09:00:00Z",
    ...over,
  };
}

function chapter(over: Partial<AgendaChapter> = {}): AgendaChapter {
  return { projectId: 10, label: "Portail", items: [raised()], ...over };
}

describe("ReviewAgendaPage", () => {
  beforeEach(() => {
    agenda.chapters = null;
    agenda.waiting = 0;
    agenda.clear = vi.fn();
    panel.openedMission = null;
    panel.open = vi.fn();
    mayWrite.value = true;
  });

  it("says where a mark is left when nothing is waiting", () => {
    agenda.chapters = [];

    render(<ReviewAgendaPage />);

    expect(screen.getByText(/Rien n'attend d'être discuté/)).toBeInTheDocument();
  });

  it("gathers a project's lines under its name, and counts them", () => {
    agenda.chapters = [
      chapter({ items: [raised(), raised({ update_id: 2 })] }),
      chapter({ projectId: 11, label: "Atlas", items: [raised({ update_id: 3 })] }),
    ];
    agenda.waiting = 3;

    render(<ReviewAgendaPage />);

    expect(
      screen.getByText("3 mises à jour à discuter, sur 2 projets."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Portail" })).toBeInTheDocument();
  });

  /**
   * Beside the list, not instead of it: one prepares a revue by going down
   * the agenda, and leaving the screen for each project would lose the place
   * every time.
   */
  it("opens the project beside the agenda, without leaving it", async () => {
    agenda.chapters = [chapter()];
    agenda.waiting = 1;

    render(<ReviewAgendaPage />);
    await userEvent.click(screen.getByRole("button", { name: "Portail" }));

    expect(panel.open).toHaveBeenCalledWith(10);
  });

  it("agrees in the singular on one line and one project", () => {
    agenda.chapters = [chapter()];
    agenda.waiting = 1;

    render(<ReviewAgendaPage />);

    expect(
      screen.getByText("1 mise à jour à discuter, sur 1 projet."),
    ).toBeInTheDocument();
  });

  it("says who raised each line, and lowers it on the gesture", async () => {
    agenda.chapters = [chapter()];

    render(<ReviewAgendaPage />);
    const line = screen.getByRole("article");

    expect(within(line).getByText(/Signalé par N. Garo/)).toBeInTheDocument();
    await userEvent.click(within(line).getByRole("button", { name: "Discuté" }));

    expect(agenda.clear).toHaveBeenCalledWith(10, 1);
  });

  it("offers no gesture to a reader who may only read", () => {
    agenda.chapters = [chapter()];
    mayWrite.value = false;

    render(<ReviewAgendaPage />);

    expect(screen.queryByRole("button", { name: "Discuté" })).not.toBeInTheDocument();
  });
});
