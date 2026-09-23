import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UserIdentityTab } from "./UserIdentityTab";
import type { UserResponse } from "@/lib/api/generated/model";
import { A_WEEK_ON_SITE } from "@/lib/presence";

const jeremy: UserResponse = {
  id: 1,
  email: "j.buget@waat.fr",
  display_name: "Jérémy Buget",
  initials: "JB",
  role: "MANAGER",
  presence: A_WEEK_ON_SITE,
  reminder_cadence: "DAILY",
  is_active: true,
  last_login_at: "2026-09-17T07:00:00Z",
};

const NOW = new Date("2026-09-17T10:00:00Z");

const onChangeRole = vi.fn();
const onUpdateIdentity = vi.fn();
const onSetActive = vi.fn();
const onDeclarePresence = vi.fn();

function openTab(
  user: Partial<UserResponse> = {},
  {
    roleModifiable = false,
    canChangeStatus = false,
    editable = false,
    isMe = false,
  } = {},
) {
  render(
    <UserIdentityTab
      user={{ ...jeremy, ...user }}
      roleModifiable={roleModifiable}
      canChangeStatus={canChangeStatus}
      editable={editable}
      isMe={isMe}
      onChangeRole={onChangeRole}
      onSetActive={onSetActive}
      onUpdateIdentity={onUpdateIdentity}
      onDeclarePresence={onDeclarePresence}
      now={NOW}
    />,
  );
}

describe("UserIdentityTab", () => {
  beforeEach(() => {
    onChangeRole.mockClear();
    onUpdateIdentity.mockClear();
    onSetActive.mockClear();
    onDeclarePresence.mockClear();
  });

  it("gives what is known of the account", () => {
    openTab();

    expect(screen.getByText("j.buget@waat.fr")).toBeInTheDocument();
    expect(screen.getByText("Manager")).toBeInTheDocument();
    expect(screen.getByText("Actif")).toBeInTheDocument();
    expect(screen.getByText("il y a 3 h")).toBeInTheDocument();
  });

  it("gives the civil name and the department", () => {
    openTab({
      first_name: "Jérémy",
      last_name: "Buget",
      department: "information_systems",
    });

    expect(screen.getByText("Jérémy")).toBeInTheDocument();
    expect(screen.getByText("Buget")).toBeInTheDocument();
    expect(screen.getByText("Système d'information")).toBeInTheDocument();
  });

  it("gives where one finds a teammate on GitHub", () => {
    openTab({ github_username: "jbuget" });

    expect(screen.getByText("jbuget")).toBeInTheDocument();
    expect(screen.getByText("github.com/")).toBeInTheDocument();
  });

  it("says what nobody has filled in yet, rather than leaving a blank", () => {
    openTab({
      first_name: null,
      last_name: null,
      department: null,
      github_username: null,
    });

    expect(screen.getAllByText("Non renseigné")).toHaveLength(4);
  });

  it("puts the week the person declares after the account", () => {
    openTab();

    expect(
      screen.getAllByRole("heading").map((heading) => heading.textContent),
    ).toEqual(["Compte", "Présence"]);
  });

  it("does not offer writing the sheet without management rights", () => {
    openTab({ first_name: "Jérémy" });

    expect(screen.queryByRole("button", { name: "Prénom" })).toBeNull();
    expect(screen.queryByRole("button", { name: /département/i })).toBeNull();
  });

  it("lets a manager give a first name", async () => {
    openTab({ first_name: null }, { editable: true });

    await userEvent.click(screen.getByRole("button", { name: "Prénom" }));
    await userEvent.type(
      screen.getByRole("textbox", { name: "Prénom" }),
      "Jérémy{Enter}",
    );

    expect(onUpdateIdentity).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }), {
      first_name: "Jérémy",
    });
  });

  it("lets a manager say where a teammate is found on GitHub", async () => {
    openTab({ github_username: null }, { editable: true });

    await userEvent.click(screen.getByRole("button", { name: "GitHub" }));
    await userEvent.type(
      screen.getByRole("textbox", { name: "GitHub" }),
      "jbuget{Enter}",
    );

    expect(onUpdateIdentity).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }), {
      github_username: "jbuget",
    });
  });

  it("lets a manager file a teammate under a department", async () => {
    openTab({ department: null }, { editable: true });

    await userEvent.click(screen.getByRole("button", { name: /département/i }));
    await userEvent.click(screen.getByRole("button", { name: "Bailleurs" }));

    expect(onUpdateIdentity).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }), {
      department: "landlords",
    });
  });

  it("tells apart an account that has never logged in", () => {
    openTab({ last_login_at: null });

    expect(screen.getByText("Jamais")).toBeInTheDocument();
  });

  it("shows the role without offering to change it, without management rights", () => {
    openTab();

    expect(screen.getByText("Manager")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });

  it("lets a manager change the role", async () => {
    openTab({}, { roleModifiable: true });

    await userEvent.click(screen.getByRole("button", { name: /Changer le rôle/ }));
    await userEvent.click(screen.getByRole("button", { name: /Collaborateur/ }));

    expect(onChangeRole).toHaveBeenCalledWith(1, "TEAMMATE");
  });

  it("does not offer cutting off access without management rights", () => {
    openTab();

    expect(screen.queryByRole("button", { name: /Désactiver/ })).toBeNull();
  });

  it("asks for confirmation before cutting off access", async () => {
    openTab({}, { canChangeStatus: true });

    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));

    // Cutting off access does not go ahead on a single click.
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(onSetActive).not.toHaveBeenCalled();
  });

  it("cuts off access once confirmation is given", async () => {
    openTab({}, { canChangeStatus: true });

    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));
    // The dialog's button, not the badge that opened it.
    await userEvent.click(screen.getByRole("button", { name: /^Désactiver$/ }));

    expect(onSetActive).toHaveBeenCalledWith(1, false);
  });

  it("restores access without confirmation, since it takes nothing away", async () => {
    openTab({ is_active: false }, { canChangeStatus: true });

    await userEvent.click(screen.getByRole("button", { name: "Réactiver ce compte" }));

    expect(onSetActive).toHaveBeenCalledWith(1, true);
  });
});
