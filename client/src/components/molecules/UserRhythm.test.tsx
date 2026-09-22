import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { UserRhythm } from "@/components/molecules/UserRhythm";
import type { WorkRhythmResponse } from "@/lib/api/generated/model";

const TODAY = new Date(2026, 8, 22);

const FOUR_FIFTHS: WorkRhythmResponse = {
  effective_from: "2026-03-01",
  monday: 1,
  tuesday: 1,
  wednesday: 0,
  thursday: 1,
  friday: 1,
  days_per_week: 4,
  is_in_force: true,
};

const THREE_DAYS: WorkRhythmResponse = {
  effective_from: "2026-10-05",
  monday: 0,
  tuesday: 0,
  wednesday: 1,
  thursday: 1,
  friday: 1,
  days_per_week: 3,
  is_in_force: false,
};

function show(
  rhythms: WorkRhythmResponse[],
  { editable = false, onDeclare = vi.fn(), onWithdraw = vi.fn() } = {},
) {
  render(
    <UserRhythm
      rhythms={rhythms}
      editable={editable}
      today={TODAY}
      onDeclare={onDeclare}
      onWithdraw={onWithdraw}
    />,
  );
  return { onDeclare, onWithdraw };
}

describe("what the panel says", () => {
  it("counts the week and dates the rhythm in force", () => {
    show([FOUR_FIFTHS]);

    expect(screen.getByText(/4 jours par semaine/)).toBeInTheDocument();
    expect(screen.getByText(/depuis le 1 mars 2026/)).toBeInTheDocument();
  });

  it("reads somebody who declared nothing as full time, and says so", () => {
    show([]);

    expect(screen.getByText(/5 jours par semaine/)).toBeInTheDocument();
    expect(screen.getByText(/rythme non déclaré/)).toBeInTheDocument();
  });

  it("does not read a rhythm opening later as the one in force", () => {
    // It would say somebody is already at three days when they are not.
    show([THREE_DAYS]);

    expect(screen.getByText(/5 jours par semaine/)).toBeInTheDocument();
    expect(screen.getByText(/rythme non déclaré/)).toBeInTheDocument();
  });
});

describe("the history one corrects", () => {
  it("lists every rhythm declared, and marks the one that holds", () => {
    show([THREE_DAYS, FOUR_FIFTHS]);

    expect(screen.getByText(/à partir du 5 oct. 2026/)).toBeInTheDocument();
    expect(screen.getByText("en vigueur")).toBeInTheDocument();
  });

  it("stays out of the way when there is only one", () => {
    // The sentence above already says it; a list of one would only repeat.
    show([FOUR_FIFTHS]);

    expect(screen.queryByText("en vigueur")).not.toBeInTheDocument();
  });

  it("offers no withdrawal on a colleague's history", () => {
    show([THREE_DAYS, FOUR_FIFTHS]);

    expect(screen.queryByLabelText(/^Retirer le rythme/)).not.toBeInTheDocument();
  });

  it("withdraws the one asked for, by the day it opens on", async () => {
    const { onWithdraw } = show([THREE_DAYS, FOUR_FIFTHS], { editable: true });

    await userEvent.click(screen.getByLabelText("Retirer le rythme du 5 oct. 2026"));

    expect(onWithdraw).toHaveBeenCalledWith("2026-10-05");
  });

  it("says so when a withdrawal is turned down", async () => {
    const refuse = vi.fn().mockRejectedValue(new Error("nope"));
    show([THREE_DAYS, FOUR_FIFTHS], { editable: true, onWithdraw: refuse });

    await userEvent.click(screen.getByLabelText("Retirer le rythme du 5 oct. 2026"));

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

describe("declaring one's own", () => {
  it("offers nothing to change on a colleague's rhythm", () => {
    show([FOUR_FIFTHS]);

    expect(
      screen.queryByRole("button", { name: "Enregistrer" }),
    ).not.toBeInTheDocument();
  });

  it("holds the motif until it is sent", async () => {
    // Three clicks to say « Wednesday off » would otherwise be three
    // declarations, and three lines in the register.
    const { onDeclare } = show([], { editable: true });

    await userEvent.click(screen.getByLabelText(/^Mercredi/));

    expect(onDeclare).not.toHaveBeenCalled();
    expect(screen.getByText(/4,5 jours par semaine/)).toBeInTheDocument();
  });

  it("sends the motif and the day it opens on", async () => {
    const { onDeclare } = show([], { editable: true });

    await userEvent.click(screen.getByLabelText(/^Mercredi/));
    await userEvent.click(screen.getByLabelText(/^Mercredi/));
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onDeclare).toHaveBeenCalledWith(
      { monday: 1, tuesday: 1, wednesday: 0, thursday: 1, friday: 1 },
      "2026-09-01",
    );
  });

  it("opens on the day the rhythm in force opened, so a correction replaces it", async () => {
    // The first of the month would slip underneath the rhythm in force, which
    // would go on covering it: the API would answer, and nothing would move.
    show([FOUR_FIFTHS], { editable: true });

    await userEvent.click(screen.getByLabelText(/^Jeudi/));

    expect(screen.getByLabelText("À partir du")).toHaveValue("2026-03-01");
  });

  it("warns when a declaration would open under the one in force", async () => {
    show([FOUR_FIFTHS], { editable: true });

    await userEvent.click(screen.getByLabelText(/^Jeudi/));
    await userEvent.clear(screen.getByLabelText("À partir du"));
    await userEvent.type(screen.getByLabelText("À partir du"), "2026-01-15");

    expect(screen.getByText(/restera en vigueur/)).toBeInTheDocument();
  });

  it("gives the date back on « Annuler », so it does not carry over", async () => {
    show([FOUR_FIFTHS], { editable: true });

    await userEvent.click(screen.getByLabelText(/^Lundi/));
    await userEvent.clear(screen.getByLabelText("À partir du"));
    await userEvent.type(screen.getByLabelText("À partir du"), "2026-12-01");
    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));
    await userEvent.click(screen.getByLabelText(/^Lundi/));

    expect(screen.getByLabelText("À partir du")).toHaveValue("2026-03-01");
  });

  it("says so when the API turns a rhythm down, and keeps the motif", async () => {
    const refuse = vi.fn().mockRejectedValue(new Error("nope"));
    show([], { editable: true, onDeclare: refuse });

    await userEvent.click(screen.getByLabelText(/^Mercredi/));
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/4,5 jours par semaine/)).toBeInTheDocument();
  });
});
