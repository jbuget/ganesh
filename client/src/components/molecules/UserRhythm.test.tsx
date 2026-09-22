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

const THREE_DAYS: WorkRhythmResponse = {
  effective_from: "2026-10-05",
  monday: 0,
  tuesday: 0,
  wednesday: 1,
  thursday: 1,
  friday: 1,
  days_per_week: 3,
};

function show(
  rhythm: WorkRhythmResponse | null,
  {
    editable = false,
    onDeclare = vi.fn(),
    upcoming = null as WorkRhythmResponse | null,
  } = {},
) {
  render(
    <UserRhythm
      rhythm={rhythm}
      upcoming={upcoming}
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

describe("a declaration that would be covered by the one in force", () => {
  it("opens on the day the rhythm in force opened, so a correction replaces it", async () => {
    // The first of the month would slip underneath the rhythm in force, which
    // would go on covering it: the API would answer, and nothing would move.
    show(FOUR_FIFTHS, { editable: true });

    await userEvent.click(screen.getByLabelText(/^Jeudi/));

    expect(screen.getByLabelText("À partir du")).toHaveValue("2026-03-01");
  });

  it("opens on the first of the month when nothing was ever declared", async () => {
    show(null, { editable: true });

    await userEvent.click(screen.getByLabelText(/^Mercredi/));

    expect(screen.getByLabelText("À partir du")).toHaveValue("2026-09-01");
  });

  it("says so rather than letting one click into the void", async () => {
    show(FOUR_FIFTHS, { editable: true });

    await userEvent.click(screen.getByLabelText(/^Jeudi/));
    await userEvent.clear(screen.getByLabelText("À partir du"));
    await userEvent.type(screen.getByLabelText("À partir du"), "2026-01-15");

    expect(screen.getByText(/restera en vigueur/)).toBeInTheDocument();
  });
});

describe("when the API turns a rhythm down", () => {
  it("says so rather than swallowing it", async () => {
    const refuse = vi.fn().mockRejectedValue(new Error("nope"));
    show(null, { editable: true, onDeclare: refuse });

    await userEvent.click(screen.getByLabelText(/^Mercredi/));
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("keeps the motif so nothing typed is lost", async () => {
    const refuse = vi.fn().mockRejectedValue(new Error("nope"));
    show(null, { editable: true, onDeclare: refuse });

    await userEvent.click(screen.getByLabelText(/^Mercredi/));
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(screen.getByText(/4,5 jours par semaine/)).toBeInTheDocument();
  });
});

describe("a rhythm declared for later", () => {
  it("is announced beside the one in force", () => {
    // Declared and shown nowhere reads as a write that failed.
    show(FOUR_FIFTHS, { upcoming: THREE_DAYS });

    expect(screen.getByText(/4 jours par semaine/)).toBeInTheDocument();
    expect(
      screen.getByText(/puis 3 jours à partir du 5 oct. 2026/),
    ).toBeInTheDocument();
  });

  it("is announced even when nothing is in force yet", () => {
    show(null, { upcoming: THREE_DAYS });

    expect(
      screen.getByText(/puis 3 jours à partir du 5 oct. 2026/),
    ).toBeInTheDocument();
  });

  it("says nothing when every rhythm has opened", () => {
    show(FOUR_FIFTHS);

    expect(screen.queryByText(/à partir du/)).not.toBeInTheDocument();
  });
});

describe("giving up on a change", () => {
  it("gives the date back too, so it does not carry into the next one", async () => {
    // A date left behind by an abandoned change would silently date the next
    // declaration, which is how a rhythm ends up opening next month.
    show(FOUR_FIFTHS, { editable: true });

    await userEvent.click(screen.getByLabelText(/^Lundi/));
    await userEvent.clear(screen.getByLabelText("À partir du"));
    await userEvent.type(screen.getByLabelText("À partir du"), "2026-12-01");
    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));
    await userEvent.click(screen.getByLabelText(/^Lundi/));

    expect(screen.getByLabelText("À partir du")).toHaveValue("2026-03-01");
  });
});
