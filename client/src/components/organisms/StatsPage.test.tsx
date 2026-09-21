import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StatsPage } from "./StatsPage";
import type { StatisticsResponse } from "@/lib/api/generated/model";

const screenState = vi.hoisted(() => ({
  range: "last_30_days" as string,
  statistics: undefined as StatisticsResponse | undefined,
  isLoading: false,
  setRange: vi.fn(),
  alerts: { lateCatchUp: false, idleTeammates: false },
}));

vi.mock("@/lib/use-statistics-screen", async () => {
  const actual = await vi.importActual<typeof import("@/lib/use-statistics-screen")>(
    "@/lib/use-statistics-screen",
  );
  return { ...actual, useStatisticsScreen: () => screenState };
});

const STATISTICS: StatisticsResponse = {
  period: {
    range: "last_30_days",
    start: "2026-08-19",
    end: "2026-09-17",
    working_days: 22,
  },
  coverage: {
    declared_days: 142,
    expected_days: 163,
    missing_days: 21,
    rate: 142 / 163,
    delta_in_points: 6,
  },
  freshness: {
    entries: 220,
    median_delay: 1.5,
    day_to_day_share: 0.68,
    late_share: 0.09,
  },
  month_validation: { validated: 9, due: 12, rate: 0.75 },
  adoption: {
    contributors: 11,
    expected_contributors: 12,
    rate: 11 / 12,
    idle: [{ id: 4, display_name: "L. Chen" }],
  },
  surfaces: {
    activities: [
      {
        surface: "time_entry",
        people: 11,
        gestures: 240,
        delta_in_people: 1,
        is_idle: false,
        last_used_on: "2026-09-17",
      },
      {
        surface: "gazette",
        people: 0,
        gestures: 0,
        delta_in_people: 0,
        is_idle: true,
        last_used_on: null,
      },
    ],
    idle_count: 1,
  },
  steering: {
    project_days: 120,
    off_project_days: 22,
    project_share: 120 / 142,
    by_status: [{ status: "development", days: 80, share: 80 / 142 }],
    by_category: [{ category: "automate_streamline", days: 60, share: 60 / 142 }],
    top_missions: [{ project_id: 7, label: "Extranet", days: 40, share: 40 / 142 }],
  },
  registry: {
    active_missions: 30,
    missions_with_time: 18,
    missions_without_time: 12,
    usage_rate: 0.6,
    created: 2,
  },
};

function renderPage(overrides: Partial<typeof screenState> = {}) {
  Object.assign(screenState, {
    range: "last_30_days",
    statistics: STATISTICS,
    isLoading: false,
    setRange: vi.fn(),
    alerts: { lateCatchUp: false, idleTeammates: false },
    ...overrides,
  });
  render(<StatsPage />);
  return screenState;
}

describe("StatsPage", () => {
  it("leads with the coverage rate", () => {
    renderPage();

    expect(screen.getByText("87 %")).toBeInTheDocument();
  });

  it("says over which days the figures were read", () => {
    renderPage();

    expect(
      screen.getByText("Du 19 août au 17 septembre 2026 · 22 jours ouvrés"),
    ).toBeInTheDocument();
  });

  it("changes window on demand", async () => {
    const state = renderPage();

    await userEvent.click(screen.getByRole("button", { name: /Plage de temps/ }));
    await userEvent.click(screen.getByRole("option", { name: /7 derniers jours/ }));

    expect(state.setRange).toHaveBeenCalledWith("last_7_days");
  });

  it("answers the three questions in order", () => {
    // Coverage first: nothing below it means anything if the data has holes.
    renderPage();

    const headings = screen
      .getAllByRole("heading", { level: 2 })
      .map((heading) => heading.textContent);
    expect(headings).toEqual([
      "Couverture de la saisie",
      "Fiabilité",
      "Adoption",
      "Fonctions utilisées",
      "Valeur de pilotage",
      "Santé du référentiel",
    ]);
  });

  it("reads every function of the product, used or not", () => {
    // The dashboard measured the entry grid alone while eleven other things
    // were built beside it.
    renderPage();

    expect(screen.getByText("Saisie des temps")).toBeInTheDocument();
    expect(screen.getByText("La Gazette")).toBeInTheDocument();
    expect(
      screen.getByText(/1 fonction n'a servi à personne sur la période\./),
    ).toBeInTheDocument();
  });

  it("names the teammates who declared nothing", () => {
    // The screen is read by everyone: a collective rate only moves when each
    // person can see their own part in it.
    renderPage();

    expect(screen.getByText("L. Chen")).toBeInTheDocument();
  });

  it("draws attention to a freshness the hook raised", () => {
    renderPage({ alerts: { lateCatchUp: true, idleTeammates: false } });

    const tile = screen.getByText("Rattrapé tardivement").closest("[data-tone]");
    expect(tile).toHaveAttribute("data-tone", "warning");
  });

  it("leaves an unraised freshness plain", () => {
    renderPage();

    const tile = screen.getByText("Rattrapé tardivement").closest("[data-tone]");
    expect(tile).toHaveAttribute("data-tone", "plain");
  });

  it("says plainly when no closed month is covered", () => {
    renderPage({
      statistics: {
        ...STATISTICS,
        month_validation: { validated: 0, due: 0, rate: null },
      },
    });

    expect(screen.getByText("aucun mois échu sur la période")).toBeInTheDocument();
  });

  it("breaks the declared time down every way it can be read", () => {
    renderPage();

    for (const title of [
      "Projet ou hors projet",
      "Temps par phase",
      "Temps par axe stratégique",
      "Projets les plus consommateurs",
    ]) {
      expect(screen.getByRole("heading", { name: title })).toBeInTheDocument();
    }
  });

  it("stays neutral over teammates the hook did not raise", () => {
    renderPage();

    const tile = screen.getByText("Sans aucune saisie").closest("[data-tone]");
    expect(tile).toHaveAttribute("data-tone", "plain");
  });

  it("draws attention to teammates the hook raised", () => {
    renderPage({ alerts: { lateCatchUp: false, idleTeammates: true } });

    const tile = screen.getByText("Sans aucune saisie").closest("[data-tone]");
    expect(tile).toHaveAttribute("data-tone", "warning");
  });

  it("says plainly when no entry at all was written", () => {
    renderPage({
      statistics: {
        ...STATISTICS,
        freshness: {
          entries: 0,
          median_delay: null,
          day_to_day_share: null,
          late_share: null,
        },
      },
    });

    expect(screen.getByText("aucune saisie écrite sur la période")).toBeInTheDocument();
  });

  it("says what the missions created were added to", () => {
    renderPage();

    expect(
      screen.getByText("ajoutées au référentiel sur la période"),
    ).toBeInTheDocument();
  });

  it("waits without pretending the figures are zero", () => {
    // Drawing a « 0 % » while loading would announce a failure that has not
    // been measured.
    renderPage({ statistics: undefined, isLoading: true });

    expect(screen.getByText("Chargement des statistiques…")).toBeInTheDocument();
    expect(screen.queryByText("0 %")).not.toBeInTheDocument();
  });

  it("offers the window selector even before the figures arrive", () => {
    renderPage({ statistics: undefined, isLoading: true });

    expect(screen.getByRole("button", { name: /Plage de temps/ })).toBeInTheDocument();
  });
});
