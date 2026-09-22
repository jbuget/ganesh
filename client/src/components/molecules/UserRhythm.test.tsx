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
};

function show(
  rhythm: WorkRhythmResponse | null,
  { editable = false, onDeclare = vi.fn() } = {},
) {
  render(
    <UserRhythm
      rhythm={rhythm}
      editable={editable}
      today={TODAY}
      onDeclare={onDeclare}
    />,
  );
  return onDeclare;
}

describe("what the panel says", () => {
  it("counts the week and dates the rhythm", () => {
    show(FOUR_FIFTHS);

    expect(screen.getByText(/4 jours par semaine/)).toBeInTheDocument();
    expect(screen.getByText(/depuis le 1 mars 2026/)).toBeInTheDocument();
  });

  it("reads somebody who declared nothing as full time, and says so", () => {
    show(null);

    expect(screen.getByText(/5 jours par semaine/)).toBeInTheDocument();
    expect(screen.getByText(/rythme non déclaré/)).toBeInTheDocument();
  });
});

describe("declaring one's own", () => {
  it("offers nothing to change on a colleague's rhythm", () => {
    show(FOUR_FIFTHS);

    expect(
      screen.queryByRole("button", { name: "Enregistrer" }),
    ).not.toBeInTheDocument();
  });

  it("holds the motif until it is sent", async () => {
    // Three clicks to say « Wednesday off » would otherwise be three
    // declarations, and three lines in the register.
    const onDeclare = show(null, { editable: true });

    await userEvent.click(screen.getByLabelText(/^Mercredi/));

    expect(onDeclare).not.toHaveBeenCalled();
    expect(screen.getByText(/4,5 jours par semaine/)).toBeInTheDocument();
  });

  it("sends the motif and the day it opens on", async () => {
    const onDeclare = show(null, { editable: true });

    await userEvent.click(screen.getByLabelText(/^Mercredi/));
    await userEvent.click(screen.getByLabelText(/^Mercredi/));
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onDeclare).toHaveBeenCalledWith(
      { monday: 1, tuesday: 1, wednesday: 0, thursday: 1, friday: 1 },
      "2026-09-01",
    );
  });

  it("gives the declared motif back when one changes their mind", async () => {
    const onDeclare = show(FOUR_FIFTHS, { editable: true });

    await userEvent.click(screen.getByLabelText(/^Lundi/));
    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));

    expect(onDeclare).not.toHaveBeenCalled();
    expect(screen.getByText(/4 jours par semaine/)).toBeInTheDocument();
  });
});
