import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DeactivateUserDialog } from "./DeactivateUserDialog";

describe("DeactivateUserDialog", () => {
  it("nomme la personne dont l'accès est coupé", () => {
    render(
      <DeactivateUserDialog
        open
        onOpenChange={vi.fn()}
        name="L. Chen"
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.getByText(/L\. Chen/)).toBeInTheDocument();
  });

  it("annonce que les saisies passées sont conservées", () => {
    // Couper l'acces n'efface rien : le dire evite d'hesiter a le faire.
    render(
      <DeactivateUserDialog
        open
        onOpenChange={vi.fn()}
        name="L. Chen"
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.getByText(/entries/)).toBeInTheDocument();
  });

  it("coupe l'accès à la confirmation", async () => {
    const onConfirm = vi.fn();
    render(
      <DeactivateUserDialog
        open
        onOpenChange={vi.fn()}
        name="L. Chen"
        onConfirm={onConfirm}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /Désactiver/ }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });
});
