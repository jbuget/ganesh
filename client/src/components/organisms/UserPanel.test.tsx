import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { UserResponse } from "@/lib/api/generated/model";

import { UserPanel } from "./UserPanel";

const jeremy: UserResponse = {
  id: 1,
  email: "j.buget@waat.fr",
  display_name: "Jérémy Buget",
  initials: "JB",
  role: "MANAGER",
  is_active: true,
  last_login_at: "2026-09-17T09:00:00",
};

const NOW = new Date("2026-09-17T12:00:00");

const onChangeRole = vi.fn();
const onUpdateIdentity = vi.fn();
const onSetActive = vi.fn();
const onClose = vi.fn();

function openPanel(
  user: Partial<UserResponse> = {},
  { roleModifiable = false, canChangeStatus = false, editable = false } = {},
) {
  render(
    <UserPanel
      user={{ ...jeremy, ...user }}
      roleModifiable={roleModifiable}
      canChangeStatus={canChangeStatus}
      editable={editable}
      onChangeRole={onChangeRole}
      onSetActive={onSetActive}
      onUpdateIdentity={onUpdateIdentity}
      now={NOW}
      onClose={onClose}
    />,
  );
}

describe("UserPanel", () => {
  beforeEach(() => {
    onChangeRole.mockClear();
    onUpdateIdentity.mockClear();
    onSetActive.mockClear();
    onClose.mockClear();
  });

  it("gives what is known of the account", () => {
    openPanel();

    expect(
      screen.getByRole("complementary", { name: "Jérémy Buget" }),
    ).toBeInTheDocument();
    expect(screen.getByText("j.buget@waat.fr")).toBeInTheDocument();
    expect(screen.getByText("Manager")).toBeInTheDocument();
    expect(screen.getByText("Actif")).toBeInTheDocument();
    expect(screen.getByText("il y a 3 h")).toBeInTheDocument();
  });

  it("gives the civil name and the department", () => {
    openPanel({
      first_name: "Jérémy",
      last_name: "Buget",
      department: "information_systems",
    });

    expect(screen.getByText("Jérémy")).toBeInTheDocument();
    expect(screen.getByText("Buget")).toBeInTheDocument();
    expect(screen.getByText("Système d'information")).toBeInTheDocument();
  });

  it("says what nobody has filled in yet, rather than leaving a blank", () => {
    openPanel({ first_name: null, last_name: null, department: null });

    expect(screen.getAllByText("Non renseigné")).toHaveLength(3);
  });

  it("does not offer writing the sheet without management rights", () => {
    openPanel({ first_name: "Jérémy" });

    expect(screen.queryByRole("button", { name: "Prénom" })).toBeNull();
    expect(screen.queryByRole("button", { name: /département/i })).toBeNull();
  });

  it("lets a manager give a first name", async () => {
    openPanel({ first_name: null }, { editable: true });

    await userEvent.click(screen.getByRole("button", { name: "Prénom" }));
    await userEvent.type(
      screen.getByRole("textbox", { name: "Prénom" }),
      "Jérémy{Enter}",
    );

    expect(onUpdateIdentity).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }), {
      first_name: "Jérémy",
    });
  });

  it("lets a manager file a teammate under a department", async () => {
    openPanel({ department: null }, { editable: true });

    await userEvent.click(screen.getByRole("button", { name: /département/i }));
    await userEvent.click(screen.getByRole("button", { name: "Bailleurs" }));

    expect(onUpdateIdentity).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }), {
      department: "landlords",
    });
  });

  it("tells apart an account that has never logged in", () => {
    openPanel({ last_login_at: null });

    expect(screen.getByText("Jamais")).toBeInTheDocument();
  });

  it("shows the role without offering to change it, without management rights", () => {
    openPanel();

    expect(screen.getByText("Manager")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });

  it("lets a manager change the role", async () => {
    openPanel({}, { roleModifiable: true });

    await userEvent.click(screen.getByRole("button", { name: /Changer le rôle/ }));
    await userEvent.click(screen.getByRole("button", { name: /Collaborateur/ }));

    expect(onChangeRole).toHaveBeenCalledWith(1, "TEAMMATE");
  });

  it("does not offer cutting off access without management rights", () => {
    openPanel();

    expect(screen.queryByRole("button", { name: /Désactiver/ })).toBeNull();
  });

  it("asks for confirmation before cutting off access", async () => {
    openPanel({}, { canChangeStatus: true });

    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));

    // Cutting off access does not go ahead on a single click.
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(onSetActive).not.toHaveBeenCalled();
  });

  it("cuts off access once confirmation is given", async () => {
    openPanel({}, { canChangeStatus: true });

    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));
    // The dialog's button, not the badge that opened it.
    await userEvent.click(screen.getByRole("button", { name: /^Désactiver$/ }));

    expect(onSetActive).toHaveBeenCalledWith(1, false);
  });

  it("restores access without confirmation, since it takes nothing away", async () => {
    openPanel({ is_active: false }, { canChangeStatus: true });

    await userEvent.click(screen.getByRole("button", { name: "Réactiver ce compte" }));

    expect(onSetActive).toHaveBeenCalledWith(1, true);
  });

  /**
   * Escape closes the panel; the confirmation opens over it. Without care,
   * one press would answer both — the dialog would close and take the panel
   * with it.
   */
  it("gives Escape to the confirmation alone while it is open", async () => {
    openPanel({}, { canChangeStatus: true });
    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));

    await userEvent.keyboard("{Escape}");

    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("closes on the cross", async () => {
    openPanel();

    await userEvent.click(screen.getByRole("button", { name: "Fermer" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
