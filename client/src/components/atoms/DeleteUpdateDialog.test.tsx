import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DeleteUpdateDialog } from "./DeleteUpdateDialog";

describe("DeleteUpdateDialog", () => {
  it("announces that the reactions go with the text", () => {
    render(<DeleteUpdateDialog open onOpenChange={vi.fn()} onConfirm={vi.fn()} />);

    expect(screen.getByText(/réactions/)).toBeInTheDocument();
  });

  it("says the line keeps its place in the thread", () => {
    // Withdrawing is not erasing: the card stays, marked « Message supprimé ».
    render(<DeleteUpdateDialog open onOpenChange={vi.fn()} onConfirm={vi.fn()} />);

    expect(screen.getByText(/gardera sa place/)).toBeInTheDocument();
  });

  it("withdraws the update on confirmation", async () => {
    const onConfirm = vi.fn();
    render(<DeleteUpdateDialog open onOpenChange={vi.fn()} onConfirm={onConfirm} />);

    await userEvent.click(screen.getByRole("button", { name: "Supprimer" }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("withdraws nothing when one backs out", async () => {
    const onConfirm = vi.fn();
    render(<DeleteUpdateDialog open onOpenChange={vi.fn()} onConfirm={onConfirm} />);

    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));

    expect(onConfirm).not.toHaveBeenCalled();
  });
});
