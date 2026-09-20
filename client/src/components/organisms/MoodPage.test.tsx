import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MoodPage } from "./MoodPage";

const mood = vi.hoisted(() => ({ state: {} as Record<string, unknown> }));

vi.mock("@/lib/use-team-mood", () => ({ useTeamMoodScreen: () => mood.state }));

function show(overrides: Record<string, unknown> = {}) {
  mood.state = {
    isLoading: false,
    today: "2026-09-18",
    headcount: 3,
    days: [],
    ...overrides,
  };
  render(<MoodPage />);
}

describe("MoodPage", () => {
  it("says the window it reads", () => {
    show();

    expect(screen.getByText("Moral de l'équipe")).toBeInTheDocument();
    expect(
      screen.getByText(/sur les quatorze derniers jours ouvrés/),
    ).toBeInTheDocument();
  });

  it("lays the fortnight out, the most recent day first", () => {
    show({
      days: [
        {
          day: "2026-09-18",
          moods: [
            {
              author: { id: 1, display_name: "Léa Chen", initials: "LC" },
              level: "good",
            },
          ],
          counts: {},
          average: 4,
          participation: 1,
        },
        {
          day: "2026-09-17",
          moods: [],
          counts: {},
          average: null,
          participation: 0,
        },
      ],
    });

    expect(screen.getByText("vendredi 18 sept.")).toBeInTheDocument();
    expect(screen.getByText("jeudi 17 sept.")).toBeInTheDocument();
    expect(screen.getByText("LC")).toBeInTheDocument();
  });

  it("opens on the record, and offers the summary beside it", () => {
    show({
      days: [
        {
          day: "2026-09-18",
          moods: [
            {
              author: { id: 1, display_name: "Léa Chen", initials: "LC" },
              level: "good",
            },
          ],
          counts: { good: 1 },
          average: 4,
          participation: 1,
        },
      ],
    });

    // The record first: one starts on the people and steps back to the shape.
    expect(screen.getByRole("tab", { name: "Récap" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tab", { name: "Tendances" })).toBeInTheDocument();
    expect(screen.getByText("LC")).toBeInTheDocument();
  });

  it("shows nothing but the wait until the window has arrived", () => {
    show({ isLoading: true });

    expect(screen.getByText("Chargement…")).toBeInTheDocument();
  });

  it("says so when the window holds no day at all", () => {
    show();

    expect(screen.getByText(/Aucun jour à afficher/)).toBeInTheDocument();
  });
});
