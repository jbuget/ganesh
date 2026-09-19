import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { LeaveWithoutSavingDialog } from "./LeaveWithoutSavingDialog";

function draw(props: Partial<Parameters<typeof LeaveWithoutSavingDialog>[0]> = {}) {
  return render(
    <LeaveWithoutSavingDialog
      open
      onOpenChange={vi.fn()}
      simulationName={null}
      onDiscard={vi.fn()}
      {...props}
    />,
  );
}

describe("LeaveWithoutSavingDialog", () => {
  it("names the simulation whose changes would be lost", () => {
    draw({ simulationName: "Priorité bailleurs" });

    expect(screen.getByText(/« Priorité bailleurs »/)).toBeInTheDocument();
  });

  it("says a hypothesis nobody named would be lost outright", () => {
    draw({ simulationName: null });

    expect(screen.getByText(/n'a jamais été enregistrée/)).toBeInTheDocument();
  });

  it("spells out what leaving costs rather than offering a bare OK", () => {
    draw();

    expect(
      screen.getByRole("button", { name: "Quitter sans enregistrer" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Rester" })).toBeInTheDocument();
  });

  it("gives up the work only when that is what was clicked", async () => {
    const onDiscard = vi.fn();
    draw({ onDiscard });

    await userEvent.click(
      screen.getByRole("button", { name: "Quitter sans enregistrer" }),
    );

    expect(onDiscard).toHaveBeenCalled();
  });

  it("staying asks for nothing to be thrown away", async () => {
    const onDiscard = vi.fn();
    const onOpenChange = vi.fn();
    draw({ onDiscard, onOpenChange });

    await userEvent.click(screen.getByRole("button", { name: "Rester" }));

    expect(onDiscard).not.toHaveBeenCalled();
    // The primitive hands the event along too: only the first argument says
    // whether the dialog is still open.
    expect(onOpenChange.mock.calls[0][0]).toBe(false);
  });

  it("shows nothing while there is nothing to warn about", () => {
    draw({ open: false });

    expect(
      screen.queryByText("Modifications non enregistrées"),
    ).not.toBeInTheDocument();
  });
});
