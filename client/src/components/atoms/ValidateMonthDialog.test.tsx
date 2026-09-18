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
      month="mars 2026"
      totalEntered={20}
      workingDays={22}
      onConfirm={onConfirm}
      {...props}
    />,
  );

  return { onOpenChange, onConfirm };
}

describe("ValidateMonthDialog", () => {
  it("announces the month concerned", () => {
    renderDialog();

    expect(screen.getByText(/mars 2026/)).toBeInTheDocument();
  });

  it("warns about missing days without blocking validation", () => {
    renderDialog({ totalEntered: 20, workingDays: 22 });

    expect(screen.getByText(/Il manque 2 jour/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Valider" })).toBeEnabled();
  });

  it("validates the month on confirmation", async () => {
    const { onConfirm } = renderDialog();

    await userEvent.click(screen.getByRole("button", { name: "Valider" }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("closes once the month is validated", async () => {
    const { onOpenChange } = renderDialog();

    await userEvent.click(screen.getByRole("button", { name: "Valider" }));

    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
  });

  it("stays open until validation succeeds", async () => {
    let release: () => void = () => {};
    const onConfirm = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          release = resolve;
        }),
    );
    const { onOpenChange } = renderDialog({ onConfirm });

    await userEvent.click(screen.getByRole("button", { name: "Valider" }));

    expect(onOpenChange).not.toHaveBeenCalledWith(false);

    release();
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
  });

  it("validates only once even on a double click", async () => {
    let release: () => void = () => {};
    const onConfirm = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          release = resolve;
        }),
    );
    renderDialog({ onConfirm });

    const button = screen.getByRole("button", { name: "Valider" });
    await userEvent.click(button);
    await userEvent.click(button);

    expect(onConfirm).toHaveBeenCalledTimes(1);
    release();
  });
});
