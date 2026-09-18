import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("names both states, rather than flagging only one", () => {
    const { rerender } = render(
      <StatusBadge is_active modifiable={false} onToggle={vi.fn()} />,
    );
    expect(screen.getByText("Actif")).toBeInTheDocument();

    rerender(<StatusBadge is_active={false} modifiable={false} onToggle={vi.fn()} />);
    expect(screen.getByText("Désactivé")).toBeInTheDocument();
  });

  it("offers no button without management rights", () => {
    render(<StatusBadge is_active modifiable={false} onToggle={vi.fn()} />);

    expect(screen.queryByRole("button")).toBeNull();
  });

  it("asks to cut off an active account", async () => {
    const onToggle = vi.fn();
    render(<StatusBadge is_active modifiable onToggle={onToggle} />);

    await userEvent.click(screen.getByRole("button", { name: /Désactiver/ }));

    expect(onToggle).toHaveBeenCalledWith(false);
  });

  it("asks to restore a deactivated account", async () => {
    const onToggle = vi.fn();
    render(<StatusBadge is_active={false} modifiable onToggle={onToggle} />);

    await userEvent.click(screen.getByRole("button", { name: /Réactiver/ }));

    expect(onToggle).toHaveBeenCalledWith(true);
  });
});
