import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UsersPage } from "./UsersPage";

const USERS = [
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
];

const state = vi.hoisted(() => ({
  isLoading: false,
  isManager: false,
  withInactive: false,
  toggleInactive: vi.fn(),
  users: [] as Record<string, unknown>[],
  find: vi.fn(),
  changeRole: vi.fn(),
  updateIdentity: vi.fn(),
  setActive: vi.fn(),
  meId: 1,
  now: new Date("2026-09-17T12:00:00"),
}));

const panel = vi.hoisted(() => ({
  openedUser: null as number | null,
  open: vi.fn(),
  close: vi.fn(),
}));

vi.mock("@/lib/use-users", () => ({ useUsersScreen: () => state }));
vi.mock("@/lib/opened-user", () => ({ useOpenedUser: () => panel }));

describe("UsersPage", () => {
  beforeEach(() => {
    state.users = USERS.map((user) => ({ ...user }));
    state.isManager = false;
    state.meId = 1;
    state.find = vi.fn(
      (id: number) => state.users.find((user) => user.id === id) ?? null,
    );
    panel.openedUser = null;
    panel.open.mockClear();
  });

  it("lists the teammates", () => {
    render(<UsersPage />);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("L. Chen")).toBeInTheDocument();
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
    render(<UsersPage />);

    expect(screen.getAllByText("Actif")).toHaveLength(2);
  });

  it("opens a teammate in the panel", async () => {
    render(<UsersPage />);

    await userEvent.click(screen.getByText("L. Chen"));

    expect(panel.open).toHaveBeenCalledWith(2);
  });

  it("holds no panel as long as none is asked for", () => {
    render(<UsersPage />);

    expect(screen.queryByRole("complementary")).toBeNull();
  });

  it("opens the panel on the teammate the address names", () => {
    panel.openedUser = 2;
    render(<UsersPage />);

    expect(screen.getByRole("complementary", { name: "L. Chen" })).toBeInTheDocument();
  });

  it("does not offer a teammate changing a role", () => {
    panel.openedUser = 2;
    state.isManager = false;
    render(<UsersPage />);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });

  it("gives the civil name and the department in the panel", () => {
    state.users[1] = {
      ...state.users[1],
      first_name: "Léa",
      department: "landlords",
    };
    panel.openedUser = 2;
    render(<UsersPage />);

    expect(screen.getByText("Léa")).toBeInTheDocument();
    expect(screen.getByText("Bailleurs")).toBeInTheDocument();
  });

  it("lets a manager change the role from the panel", () => {
    panel.openedUser = 2;
    state.isManager = true;
    render(<UsersPage />);

    expect(screen.getByRole("button", { name: /Changer le rôle/ })).toBeInTheDocument();
  });

  it("lets a manager cut off another's access, never their own", () => {
    // Deactivating oneself is locking oneself out: the API refuses it, and the
    // screen has no business offering a move that will be rejected.
    state.isManager = true;
    state.meId = 1;

    panel.openedUser = 1;
    const own = render(<UsersPage />);
    expect(screen.queryByRole("button", { name: "Désactiver ce compte" })).toBeNull();
    own.unmount();

    panel.openedUser = 2;
    render(<UsersPage />);
    expect(
      screen.getByRole("button", { name: "Désactiver ce compte" }),
    ).toBeInTheDocument();
  });

  it("announces an empty list rather than a table with no rows", () => {
    state.users = [];
    render(<UsersPage />);

    expect(screen.getByText(/Aucun utilisateur/)).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });
});
