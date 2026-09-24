import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
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
  users: [] as Record<string, unknown>[],
  visible: 2,
  total: 2,
  find: vi.fn(),
  changeRole: vi.fn(),
  updateIdentity: vi.fn(),
  setActive: vi.fn(),
  me: { id: 1, role: "MANAGER" } as { id: number; role: string },
  declare: vi.fn(),
  now: new Date("2026-09-17T12:00:00"),
}));

const panel = vi.hoisted(() => ({
  openedUser: null as number | null,
  open: vi.fn(),
  close: vi.fn(),
}));

const criteria = vi.hoisted(() => ({
  filters: { name: "", roles: [] as string[], states: [] as string[] },
  hasFilter: false,
  set: vi.fn(),
  clear: vi.fn(),
}));

const order = vi.hoisted(() => ({
  sorted: { column: null as string | null, direction: "asc" as const },
  toggle: vi.fn(),
}));

vi.mock("@/lib/use-users", () => ({ useUsersScreen: () => state }));
/** The panel reads a record of its own; what it draws from it is tested there. */
vi.mock("@/lib/api/queries", () => ({
  useUserRecord: () => ({
    record: {
      user_id: 1,
      missions: [],
      declared: { since: "2026-08-19", until: "2026-09-17", days: 0, missions: [] },
      months: [],
    },
    isLoading: false,
  }),
}));
vi.mock("@/lib/opened-user", () => ({ useOpenedUser: () => panel }));
vi.mock("@/lib/use-user-filters", () => ({ useUserFilters: () => criteria }));
vi.mock("@/lib/use-user-sort", () => ({ useUserSort: () => order }));

describe("UsersPage", () => {
  beforeEach(() => {
    state.users = USERS.map((user) => ({ ...user }));
    state.isManager = false;
    // Who is reading, by default: a teammate. The panel offers what it offers
    // on the rank of the reader, not on a flag beside it.
    state.me = { id: 3, role: "TEAMMATE" };
    state.find = vi.fn(
      (id: number) => state.users.find((user) => user.id === id) ?? null,
    );
    panel.openedUser = null;
    panel.open.mockClear();
    criteria.filters = { name: "", roles: [], states: [] };
    criteria.hasFilter = false;
    criteria.set.mockClear();
    order.sorted = { column: null, direction: "asc" };
    order.toggle.mockClear();
  });

  it("lists the teammates", () => {
    render(<UsersPage />);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("L. Chen")).toBeInTheDocument();
  });

  it("makes it possible to bring up deactivated accounts", async () => {
    render(<UsersPage />);

    // The filter bar, not the column of the same name: the two are told apart
    // on screen by where they sit, and here by the search group around them.
    const bar = within(screen.getByRole("search"));
    await userEvent.click(bar.getByRole("button", { name: "Statut" }));
    await userEvent.click(screen.getByRole("button", { name: "Désactivés" }));

    expect(criteria.set).toHaveBeenCalledWith({ states: ["inactive"] });
  });

  it("searches a colleague by name or by email", async () => {
    render(<UsersPage />);

    await userEvent.type(
      screen.getByRole("searchbox", { name: "Rechercher un collaborateur" }),
      "z",
    );

    expect(criteria.set).toHaveBeenCalledWith({ name: "z" });
  });

  it("arranges the list by the column whose title is clicked", async () => {
    render(<UsersPage />);

    await userEvent.click(
      within(screen.getByRole("columnheader", { name: "Rôle" })).getByRole("button"),
    );

    expect(order.toggle).toHaveBeenCalledWith("role");
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
    // The screen reads the account rather than a flag: what may be moved
    // depends on the rank of whoever is looking, not only on being a manager.
    panel.openedUser = 2;
    state.isManager = false;
    state.me = { id: 3, role: "TEAMMATE" };
    render(<UsersPage />);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });

  it("does not offer a manager touching an admin", () => {
    panel.openedUser = 2;
    state.isManager = true;
    state.me = { id: 1, role: "MANAGER" };
    state.users = [state.users[0], { ...state.users[1], role: "ADMIN" }];
    render(<UsersPage />);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Désactiver ce compte" })).toBeNull();
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
    state.me = { id: 1, role: "MANAGER" };
    render(<UsersPage />);

    expect(screen.getByRole("button", { name: /Changer le rôle/ })).toBeInTheDocument();
  });

  it("lets a manager cut off another's access, never their own", () => {
    // Deactivating oneself is locking oneself out: the API refuses it, and the
    // screen has no business offering a move that will be rejected.
    state.isManager = true;
    state.me = { id: 1, role: "MANAGER" };

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

  it("says a filter is what empties the list, not an empty team", () => {
    // « Aucun utilisateur » before a filter that keeps nobody would send one
    // looking for a bug in the accounts rather than at the criteria set.
    state.users = [];
    criteria.hasFilter = true;
    render(<UsersPage />);

    expect(
      screen.getByText(/Aucun collaborateur ne répond aux filtres/),
    ).toBeInTheDocument();
  });
});
