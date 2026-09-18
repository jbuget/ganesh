import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DeactivateUserDialog } from "./DeactivateUserDialog";

describe("DeactivateUserDialog", () => {
  it("names the person whose access is cut off", () => {
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

  it("announces that past entries are kept", () => {
    // Cutting off access erases nothing: saying so saves hesitating over it.
    render(
      <DeactivateUserDialog
        open
        onOpenChange={vi.fn()}
        name="L. Chen"
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.getByText(/saisies/)).toBeInTheDocument();
  });

  it("cuts off access on confirmation", async () => {
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
