import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RolePicker } from "./RolePicker";

describe("RolePicker", () => {
  it("affiche le rôle courant", () => {
    render(<RolePicker role="MANAGER" modifiable onChange={vi.fn()} />);

    expect(screen.getByRole("button", { name: /Manager/ })).toBeInTheDocument();
  });

  it("n'offre aucun bouton quand le rôle n'est pas modifiable", () => {
    render(<RolePicker role="TEAMMATE" modifiable={false} onChange={vi.fn()} />);

    expect(screen.getByText("Collaborateur")).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("change le rôle au choix d'un autre", async () => {
    const onChange = vi.fn();
    render(<RolePicker role="TEAMMATE" modifiable onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: /Collaborateur/ }));
    await userEvent.click(screen.getByRole("button", { name: /Manager/ }));

    expect(onChange).toHaveBeenCalledWith("MANAGER");
  });

  it("ne rejoue pas le rôle déjà porté", async () => {
    const onChange = vi.fn();
    render(<RolePicker role="MANAGER" modifiable onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: /Manager/ }));
    await userEvent.click(
      screen.getAllByRole("button", { name: /Manager/ }).at(-1) as HTMLElement,
    );

    expect(onChange).not.toHaveBeenCalled();
  });
});
