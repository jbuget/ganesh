import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ActivitySummaryPage } from "./ActivitySummaryPage";
import type {
  ActivityLineResponse,
  ActivitySummaryResponse,
} from "@/lib/api/generated/model";

const screenState = vi.hoisted(() => ({
  range: "last_week" as string,
  view: "project" as string,
  summary: undefined as ActivitySummaryResponse | undefined,
  isLoading: false,
  setRange: vi.fn(),
  setView: vi.fn(),
}));

vi.mock("@/lib/use-activity-summary", async () => {
  const actual = await vi.importActual<typeof import("@/lib/use-activity-summary")>(
    "@/lib/use-activity-summary",
  );
  return { ...actual, useActivityScreen: () => screenState };
});

function aLine(over: Partial<ActivityLineResponse> = {}): ActivityLineResponse {
  return {
    project_id: 1,
    label: "WAATcher",
    kind: "project",
    status: "development",
    category: null,
    days_by_contributor: { 1: 3 },
    own_days_by_contributor: { 1: 3 },
    days: 3,
    own_days: 3,
    share: 0.6,
    movement: 1,
    is_new: false,
    packages: [],
    ...over,
  };
}

const SUMMARY: ActivitySummaryResponse = {
  period: {
    range: "last_week",
    start: "2026-09-07",
    end: "2026-09-13",
    working_days: 5,
  },
  contributors: [
    {
      id: 1,
      display_name: "A. Ba",
      declared_days: 5,
      expected_days: 5,
      coverage: 1,
      missions: 2,
    },
    {
      id: 2,
      display_name: "B. Cy",
      declared_days: 0,
      expected_days: 5,
      coverage: 0,
      missions: 0,
    },
  ],
  projects: [aLine()],
  off_project: [
    aLine({
      project_id: 9,
      label: "Congés",
      kind: "off_project",
      status: null,
      days_by_contributor: { 1: 2 },
      own_days_by_contributor: { 1: 2 },
      days: 2,
      own_days: 2,
      share: 0.4,
      movement: 0,
      is_new: true,
    }),
  ],
  project_days: 3,
  off_project_days: 2,
  declared_days: 5,
  expected_days: 10,
  coverage: 0.5,
};

describe("ActivitySummaryPage", () => {
  beforeEach(() => {
    // The state is shared across tests: reset it, or a test reads the view
    // the one before it left behind.
    screenState.summary = SUMMARY;
    screenState.view = "project";
    screenState.setView.mockClear();
  });

  it("says the summary is unavailable rather than drawing an empty matrix", () => {
    screenState.summary = undefined;

    render(<ActivitySummaryPage />);

    expect(screen.getByText("Synthèse indisponible.")).toBeInTheDocument();
  });

  it("opens on the coverage the figures rest on", () => {
    // Read against a thin coverage, every figure below it is a fiction.
    render(<ActivitySummaryPage />);

    expect(screen.getByText("50 %")).toBeInTheDocument();
  });

  it("names those who declared nothing", () => {
    render(<ActivitySummaryPage />);

    expect(screen.getByText(/N'a rien déclaré : B\. Cy/)).toBeInTheDocument();
  });

  it("keeps missions and what happens around them in two blocks", () => {
    render(<ActivitySummaryPage />);

    expect(screen.getByRole("heading", { name: "Projets" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Hors projet" })).toBeInTheDocument();
    expect(screen.getByText("WAATcher")).toBeInTheDocument();
    expect(screen.getByText("Congés")).toBeInTheDocument();
  });

  it("makes every teammate a column, those who declared nothing included", () => {
    render(<ActivitySummaryPage />);

    expect(screen.getAllByRole("columnheader", { name: "B. Cy" }).length).toBe(2);
  });

  it("offers the other reading of the same figures", async () => {
    render(<ActivitySummaryPage />);
    await userEvent.click(screen.getByRole("tab", { name: "Par personne" }));

    expect(screenState.setView).toHaveBeenCalledWith("person");
  });

  it("reads what each person declared against what was expected", () => {
    screenState.view = "person";

    render(<ActivitySummaryPage />);

    expect(screen.getByRole("columnheader", { name: "Attendu" })).toBeInTheDocument();
  });
});
