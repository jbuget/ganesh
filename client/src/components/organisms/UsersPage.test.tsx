import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UsersPage } from "./UsersPage";

const ecran = vi.hoisted(() => ({
  isLoading: false,
  isManager: false,
  avecInactifs: false,
  basculerInactifs: vi.fn(),
  collaborateurs: [
    {
      id: 1,
      email: "j.buget@waat.fr",
      display_name: "Jérémy Buget",
      initiales: "JB",
      role: "MANAGER",
      actif: true,
    },
    {
      id: 2,
      email: "l.chen@waat.fr",
      display_name: "L. Chen",
      initiales: "LC",
      role: "TEAMMATE",
      actif: true,
    },
  ],
  changerRole: vi.fn(),
}));

vi.mock("@/lib/use-users", () => ({ useUsersScreen: () => ecran }));

describe("UsersPage", () => {
  it("liste les collaborateurs", () => {
    render(<UsersPage />);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("L. Chen")).toBeInTheDocument();
  });

  it("n'offre pas de changer un rôle à un collaborateur", () => {
    ecran.isManager = false;
    render(<UsersPage />);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });

  it("laisse un manager changer les rôles", () => {
    ecran.isManager = true;
    render(<UsersPage />);

    expect(screen.getAllByRole("button", { name: /Changer le rôle/ })).toHaveLength(2);
  });

  it("permet de faire apparaître les comptes désactivés", async () => {
    ecran.avecInactifs = false;
    render(<UsersPage />);

    await userEvent.click(
      screen.getByRole("button", { name: "Afficher les inactifs" }),
    );

    expect(ecran.basculerInactifs).toHaveBeenCalledTimes(1);
  });

  it("annonce une liste vide plutôt qu'un tableau sans ligne", () => {
    ecran.collaborateurs = [];
    render(<UsersPage />);

    expect(screen.getByText(/Aucun collaborateur/)).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });
});
