import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { HomePage } from "./HomePage";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";

const listed = (
  id: number,
  label: string,
  fields: Partial<ProjectListItemResponse> = {},
): ProjectListItemResponse =>
  ({
    project: {
      id,
      label,
      kind: "project",
      status: "development",
      parent_id: null,
      is_active: true,
      priority: "high",
      estimated_days: null,
    },
    contributors: [],
    leads: [],
    latest_update: null,
    ...fields,
  }) as ProjectListItemResponse;

const home = vi.hoisted(() => ({
  state: {} as Record<string, unknown>,
}));
const mood = vi.hoisted(() => ({
  state: {} as Record<string, unknown>,
}));

vi.mock("@/lib/use-home", () => ({ useHome: () => home.state }));
vi.mock("@/lib/use-mood", () => ({ useMood: () => mood.state }));
// The presence block reads the team, and the panel writes to it; the screen
// is tested without a QueryClient around it, as every other block here is.
vi.mock("@/lib/use-users", () => ({
  useUsersScreen: () => ({
    users: [],
    isManager: false,
    meId: 1,
    now: new Date("2026-09-17T12:00:00"),
    find: () => null,
    changeRole: vi.fn(),
    setActive: vi.fn(),
    updateIdentity: vi.fn(),
    declareOwnPresence: vi.fn(),
  }),
}));
vi.mock("@/lib/opened-user", () => ({
  useOpenedUser: () => ({ openedUser: null, open: vi.fn(), close: vi.fn() }),
}));
vi.mock("@/lib/opened-mission", () => ({
  useOpenedMission: () => ({
    openedMission: null,
    openTab: null,
    open: vi.fn(),
    close: vi.fn(),
  }),
}));

function show(
  overrides: Record<string, unknown> = {},
  moodOverrides: Record<string, unknown> = {},
) {
  mood.state = {
    isLoading: false,
    days: [],
    today: "2026-09-19",
    savingDay: null,
    post: vi.fn(),
    ...moodOverrides,
  };
  home.state = {
    me: { id: 1, display_name: "Jérémy Buget" },
    today: "2026-09-19",
    cursor: { year: 2026, month: 9 },
    isLoading: false,
    refresh: vi.fn(),
    actualDays: 12,
    forecastDays: 0,
    workingDays: 22,
    monthsToSettle: [],
    daysMissing: [],
    missionsToDeclare: [],
    mine: [],
    updates: [],
    ...overrides,
  };
  render(<HomePage />);
}

describe("HomePage", () => {
  it("greets by first name: the screen one lands on is one's own", () => {
    show();

    expect(screen.getByText(/Bonjour Jérémy/)).toBeInTheDocument();
  });

  it("shows the missions one works on", () => {
    show({
      mine: [
        {
          item: listed(1, "Portail bailleurs"),
          days: 6,
          isContributor: true,
          parentLabel: null,
        },
      ],
    });

    expect(
      screen.getByRole("button", { name: "Portail bailleurs" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/6 j/)).toBeInTheDocument();
  });

  it("says so when one works on nothing, rather than showing a bare grid", () => {
    show();

    expect(screen.getByText(/Aucun projet ne vous est assigné/)).toBeInTheDocument();
  });

  it("carries the news published on one's missions", () => {
    show({
      updates: [
        {
          item: listed(1, "Portail bailleurs"),
          update: {
            author: { id: 9, display_name: "Marie Martin", initials: "MM" },
            body: "Recette terminée",
            published_at: "2026-09-18T08:00:00Z",
          },
        },
      ],
    });

    expect(screen.getByText("Recette terminée")).toBeInTheDocument();
    expect(screen.getByText(/Marie Martin/)).toBeInTheDocument();
  });

  it("says so when no thread has moved", () => {
    show();

    expect(screen.getByText(/Aucune nouvelle publiée/)).toBeInTheDocument();
  });

  it("shows nothing but the wait until the months have arrived", () => {
    // Every block reads « nothing to report » from an empty answer: rendered
    // too early, the screen would claim all is well before it knows.
    show({ isLoading: true });

    expect(screen.getByText("Chargement…")).toBeInTheDocument();
    expect(
      screen.queryByText(/Aucun projet ne vous est assigné/),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Quoi de neuf/)).not.toBeInTheDocument();
  });

  it("asks how the day went, and does so first", () => {
    show({}, { days: [{ day: "2026-09-19", level: null }] });

    expect(screen.getByText("Mon moral")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Bonne" })).toBeInTheDocument();
  });

  it("asks how the day went even while the months load", () => {
    // The mood carries its own query: holding it behind four grids would
    // close the window on whoever lands while they are still travelling.
    show({ isLoading: true }, { days: [{ day: "2026-09-19", level: null }] });

    expect(screen.getByText("Chargement…")).toBeInTheDocument();
    expect(screen.getByText("Mon moral")).toBeInTheDocument();
  });
});
