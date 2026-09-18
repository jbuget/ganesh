import { beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Table, TableBody } from "@/components/ui/table";
import type { UserResponse } from "@/lib/api/generated/model";

import { UserRow } from "./UserRow";

const jeremy: UserResponse = {
  id: 1,
  email: "j.buget@waat.fr",
  display_name: "Jérémy Buget",
  initials: "JB",
  role: "MANAGER",
  is_active: true,
};

const MAINTENANT = new Date("2026-09-17T12:00:00");

const onSetActive = vi.fn();

function renderRow(
  user: UserResponse,
  roleModifiable = false,
  statutModifiable = false,
) {
  return render(
    <Table>
      <TableBody>
        <UserRow
          user={user}
          roleModifiable={roleModifiable}
          statutModifiable={statutModifiable}
          onChangeRole={vi.fn()}
          onSetActive={onSetActive}
          maintenant={MAINTENANT}
        />
      </TableBody>
    </Table>,
  );
}

describe("UserRow", () => {
  beforeEach(() => onSetActive.mockClear());

  it("shows the teammate, their email and their role", () => {
    renderRow(jeremy);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("j.buget@waat.fr")).toBeInTheDocument();
    expect(screen.getByText("Manager")).toBeInTheDocument();
  });

  it("names the status in both cases", () => {
    renderRow(jeremy);
    expect(screen.getByText("Actif")).toBeInTheDocument();

    cleanup();
    renderRow({ ...jeremy, is_active: false });
    expect(screen.getByText("Désactivé")).toBeInTheDocument();
  });

  it("does not offer cutting off access without management rights", () => {
    renderRow(jeremy, false, false);

    expect(screen.queryByRole("button", { name: /Désactiver/ })).toBeNull();
  });

  it("asks for confirmation before cutting off access", async () => {
    renderRow(jeremy, true, true);

    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));

    // Cutting off access does not go ahead on a single click.
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(onSetActive).not.toHaveBeenCalled();
  });

  it("cuts off access once confirmation is given", async () => {
    renderRow(jeremy, true, true);

    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));
    // The dialog's button, not the badge that opened it.
    await userEvent.click(screen.getByRole("button", { name: /^Désactiver$/ }));

    expect(onSetActive).toHaveBeenCalledWith(1, false);
  });

  it("restores access without confirmation, since it takes nothing away", async () => {
    renderRow({ ...jeremy, is_active: false }, true, true);

    await userEvent.click(screen.getByRole("button", { name: "Réactiver ce compte" }));

    expect(onSetActive).toHaveBeenCalledWith(1, true);
  });

  it("lets a manager change the role", () => {
    renderRow(jeremy, true);

    expect(screen.getByRole("button", { name: /Changer le rôle/ })).toBeInTheDocument();
  });

  it("does not offer changing the role without management rights", () => {
    renderRow(jeremy, false);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });

  it("says how long since the account last logged in", () => {
    renderRow({ ...jeremy, last_login_at: "2026-09-17T09:00:00" });

    expect(screen.getByText("il y a 3 h")).toBeInTheDocument();
  });

  it("tells apart an account that has never logged in", () => {
    renderRow({ ...jeremy, last_login_at: null });

    expect(screen.getByText("Jamais")).toBeInTheDocument();
  });
});
