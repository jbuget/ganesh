import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ReopenMonthDialog } from "./ReopenMonthDialog";

function renderDialog(props: Partial<Parameters<typeof ReopenMonthDialog>[0]> = {}) {
  const onOpenChange = vi.fn();
  const onConfirm = vi.fn().mockResolvedValue(undefined);

  render(
    <ReopenMonthDialog
      open
      onOpenChange={onOpenChange}
      month="mars 2026"
      teammate={null}
      onConfirm={onConfirm}
      {...props}
    />,
  );

  return { onOpenChange, onConfirm };
}

describe("ReopenMonthDialog", () => {
  it("announces the month concerned", () => {
    renderDialog();

    expect(screen.getByText(/mars 2026/)).toBeInTheDocument();
  });

  /** Reopening someone else's month is the ordinary case: it must say whose. */
  it("names the teammate whose month is being reopened", () => {
    renderDialog({ teammate: "Camille Roy" });

    expect(screen.getByText(/Camille Roy/)).toBeInTheDocument();
  });

  it("speaks of one's own month without naming anyone", () => {
    renderDialog({ teammate: null });

    expect(screen.getByText(/votre mois/i)).toBeInTheDocument();
  });

  /** The move is traced: saying so is what makes the lock a discipline. */
  it("says the reopening is recorded", () => {
    renderDialog();

    expect(screen.getByText(/journal/i)).toBeInTheDocument();
  });

  it("reopens the month on confirmation", async () => {
    const { onConfirm } = renderDialog();

    await userEvent.click(screen.getByRole("button", { name: "Rouvrir" }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("closes once the month is reopened", async () => {
    const { onOpenChange } = renderDialog();

    await userEvent.click(screen.getByRole("button", { name: "Rouvrir" }));

    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
  });

  /** A refusal from the API must stay before the eyes, not vanish with the window. */
  it("stays open until the reopening succeeds", async () => {
    let release: () => void = () => {};
    const onConfirm = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          release = resolve;
        }),
    );
    const { onOpenChange } = renderDialog({ onConfirm });

    await userEvent.click(screen.getByRole("button", { name: "Rouvrir" }));

    expect(onOpenChange).not.toHaveBeenCalledWith(false);

    release();
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
  });

  it("reopens only once even on a double click", async () => {
    let release: () => void = () => {};
    const onConfirm = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          release = resolve;
        }),
    );
    renderDialog({ onConfirm });

    const button = screen.getByRole("button", { name: "Rouvrir" });
    await userEvent.click(button);
    await userEvent.click(button);

    expect(onConfirm).toHaveBeenCalledTimes(1);
    release();
  });
});
