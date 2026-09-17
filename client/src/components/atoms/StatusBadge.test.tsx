import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("nomme les deux états, plutôt que de n'en signaler qu'un", () => {
    const { rerender } = render(
      <StatusBadge is_active modifiable={false} onToggle={vi.fn()} />,
    );
    expect(screen.getByText("Actif")).toBeInTheDocument();

    rerender(<StatusBadge is_active={false} modifiable={false} onToggle={vi.fn()} />);
    expect(screen.getByText("Désactivé")).toBeInTheDocument();
  });

  it("n'offre aucun bouton sans droit de gestion", () => {
    render(<StatusBadge is_active modifiable={false} onToggle={vi.fn()} />);

    expect(screen.queryByRole("button")).toBeNull();
  });

  it("demande la coupure d'accès d'un compte actif", async () => {
    const onToggle = vi.fn();
    render(<StatusBadge is_active modifiable onToggle={onToggle} />);

    await userEvent.click(screen.getByRole("button", { name: /Désactiver/ }));

    expect(onToggle).toHaveBeenCalledWith(false);
  });

  it("demande le rétablissement d'un compte désactivé", async () => {
    const onToggle = vi.fn();
    render(<StatusBadge is_active={false} modifiable onToggle={onToggle} />);

    await userEvent.click(screen.getByRole("button", { name: /Réactiver/ }));

    expect(onToggle).toHaveBeenCalledWith(true);
  });
});
