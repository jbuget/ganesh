import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UsersPage } from "./UsersPage";

const state = vi.hoisted(() => ({
  isLoading: false,
  isManager: false,
  withInactive: false,
  toggleInactive: vi.fn(),
  users: [
    {
      id: 1,
      email: "j.buget@waat.fr",
      display_name: "Jérémy Buget",
      initials: "JB",
      role: "MANAGER",
      is_active: true,
      last_login_at: "2026-09-17T09:00:00",
    },
    {
      id: 2,
      email: "l.chen@waat.fr",
      display_name: "L. Chen",
      initials: "LC",
      role: "TEAMMATE",
      is_active: true,
      last_login_at: null,
    },
  ],
  changeRole: vi.fn(),
  setActive: vi.fn(),
  meId: 1,
  now: new Date("2026-09-17T12:00:00"),
}));

vi.mock("@/lib/use-users", () => ({ useUsersScreen: () => state }));

describe("UsersPage", () => {
  it("lists the teammates", () => {
    render(<UsersPage />);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("L. Chen")).toBeInTheDocument();
  });

  it("does not offer a teammate changing a role", () => {
    state.isManager = false;
    render(<UsersPage />);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });

  it("lets a manager change the roles", () => {
    state.isManager = true;
    render(<UsersPage />);

    expect(screen.getAllByRole("button", { name: /Changer le rôle/ })).toHaveLength(2);
  });

  it("makes it possible to bring up deactivated accounts", async () => {
    state.withInactive = false;
    render(<UsersPage />);

    await userEvent.click(
      screen.getByRole("button", { name: "Afficher les inactifs" }),
    );

    expect(state.toggleInactive).toHaveBeenCalledTimes(1);
  });

  it("gives everyone's last login", () => {
    render(<UsersPage />);

    expect(
      screen.getByRole("columnheader", { name: "Dernière connexion" }),
    ).toBeInTheDocument();
    expect(screen.getByText("il y a 3 h")).toBeInTheDocument();
    expect(screen.getByText("Jamais")).toBeInTheDocument();
  });

  it("names the status of each account", () => {
    state.isManager = false;
    render(<UsersPage />);

    expect(screen.getAllByText("Actif")).toHaveLength(2);
  });

  it("lets a manager cut off another's access, never their own", () => {
    // Deactivating oneself is locking oneself out: the API refuses it, and the
    // screen has no business offering a move that will be rejected.
    state.isManager = true;
    state.meId = 1;
    render(<UsersPage />);

    const buttons = screen.getAllByRole("button", { name: "Désactiver ce compte" });
    expect(buttons).toHaveLength(1);
  });

  it("announces an empty list rather than a table with no rows", () => {
    state.users = [];
    render(<UsersPage />);

    expect(screen.getByText(/Aucun utilisateur/)).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });
});
