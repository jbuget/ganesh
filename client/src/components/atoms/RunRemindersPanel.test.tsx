import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RunRemindersPanel } from "@/components/atoms/RunRemindersPanel";

const runs = vi.hoisted(() => ({ state: {} as Record<string, unknown> }));

vi.mock("@/lib/use-reminders", () => ({ useReminderRuns: () => runs.state }));

function show(overrides: Record<string, unknown> = {}) {
  runs.state = { isRunning: false, outcome: null, run: vi.fn(), ...overrides };
  render(<RunRemindersPanel />);
  return runs.state;
}

describe("RunRemindersPanel", () => {
  it("offers one button per round, each naming its own", () => {
    // « chaque jour » and « chaque semaine » are two different sets of
    // readers: naming the round in the gesture is what stops somebody writing
    // to the weekly ones on a Tuesday.
    show();

    expect(
      screen.getByRole("button", { name: /tournée « chaque jour »/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /tournée « chaque semaine »/i }),
    ).toBeInTheDocument();
  });

  it("never offers to send the round nobody asked for", () => {
    show();

    expect(screen.queryByRole("button", { name: /jamais/i })).not.toBeInTheDocument();
  });

  it("says the clock already does this, and why one would do it by hand", () => {
    show();

    expect(screen.getByText(/chaque jour ouvré/)).toBeInTheDocument();
    expect(screen.getByText(/rattraper une matinée manquée/)).toBeInTheDocument();
  });

  it("sends the round one picks", async () => {
    const state = show();

    await userEvent.click(
      screen.getByRole("button", { name: /tournée « chaque semaine »/i }),
    );

    expect(state.run).toHaveBeenCalledWith("WEEKLY");
  });

  it("takes no second press while a round is in flight", async () => {
    const state = show({ isRunning: true });

    expect(
      screen.getByRole("button", { name: /tournée « chaque jour »/i }),
    ).toBeDisabled();
    await userEvent.click(
      screen.getByRole("button", { name: /tournée « chaque jour »/i }),
    );

    expect(state.run).not.toHaveBeenCalled();
  });

  it("says how many letters went out", () => {
    show({ outcome: { kind: "sent", message: "3 lettres envoyées." } });

    expect(screen.getByText("3 lettres envoyées.")).toBeInTheDocument();
  });

  it("says plainly when there was nothing to send", () => {
    // Not a failure: the round works and found nothing new.
    show({
      outcome: {
        kind: "nothing",
        message: "Aucune lettre : personne n'a de nouveauté en attente.",
      },
    });

    expect(screen.getByText(/Aucune lettre/)).toBeInTheDocument();
  });

  it("tells a configuration problem apart from a quiet round", () => {
    show({
      outcome: { kind: "unreachable", message: "Aucun envoi possible : …" },
    });

    expect(screen.getByText(/Aucun envoi possible/)).toHaveClass("text-red-600");
  });
});
