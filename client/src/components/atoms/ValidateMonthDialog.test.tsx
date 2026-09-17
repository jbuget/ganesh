import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ValidateMonthDialog } from "./ValidateMonthDialog";

function renderDialog(props: Partial<Parameters<typeof ValidateMonthDialog>[0]> = {}) {
  const onOpenChange = vi.fn();
  const onConfirm = vi.fn().mockResolvedValue(undefined);

  render(
    <ValidateMonthDialog
      open
      onOpenChange={onOpenChange}
      mois="mars 2026"
      totalSaisi={20}
      joursOuvres={22}
      onConfirm={onConfirm}
      {...props}
    />,
  );

  return { onOpenChange, onConfirm };
}

describe("ValidateMonthDialog", () => {
  it("annonce le mois concerné", () => {
    renderDialog();

    expect(screen.getByText(/mars 2026/)).toBeInTheDocument();
  });

  it("alerte sur les jours manquants sans bloquer la validation", () => {
    renderDialog({ totalSaisi: 20, joursOuvres: 22 });

    expect(screen.getByText(/Il manque 2 jour/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Valider" })).toBeEnabled();
  });

  it("valide le mois à la confirmation", async () => {
    const { onConfirm } = renderDialog();

    await userEvent.click(screen.getByRole("button", { name: "Valider" }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("se referme une fois le mois validé", async () => {
    const { onOpenChange } = renderDialog();

    await userEvent.click(screen.getByRole("button", { name: "Valider" }));

    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
  });

  it("reste ouvert tant que la validation n'a pas abouti", async () => {
    let resoudre: () => void = () => {};
    const onConfirm = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resoudre = resolve;
        }),
    );
    const { onOpenChange } = renderDialog({ onConfirm });

    await userEvent.click(screen.getByRole("button", { name: "Valider" }));

    expect(onOpenChange).not.toHaveBeenCalledWith(false);

    resoudre();
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
  });

  it("ne valide qu'une fois même sur double-clic", async () => {
    let resoudre: () => void = () => {};
    const onConfirm = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resoudre = resolve;
        }),
    );
    renderDialog({ onConfirm });

    const bouton = screen.getByRole("button", { name: "Valider" });
    await userEvent.click(bouton);
    await userEvent.click(bouton);

    expect(onConfirm).toHaveBeenCalledTimes(1);
    resoudre();
  });
});
