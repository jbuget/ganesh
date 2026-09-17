import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UsersPage } from "./UsersPage";

const vue = vi.hoisted(() => ({
  isLoading: false,
  isManager: false,
  avecInactifs: false,
  basculerInactifs: vi.fn(),
  collaborateurs: [
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
  changerRole: vi.fn(),
  changerActivite: vi.fn(),
  moiId: 1,
  maintenant: new Date("2026-09-17T12:00:00"),
}));

vi.mock("@/lib/use-users", () => ({ useUsersScreen: () => vue }));

describe("UsersPage", () => {
  it("liste les collaborateurs", () => {
    render(<UsersPage />);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("L. Chen")).toBeInTheDocument();
  });

  it("n'offre pas de changer un rôle à un collaborateur", () => {
    vue.isManager = false;
    render(<UsersPage />);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });

  it("laisse un manager changer les rôles", () => {
    vue.isManager = true;
    render(<UsersPage />);

    expect(screen.getAllByRole("button", { name: /Changer le rôle/ })).toHaveLength(2);
  });

  it("permet de faire apparaître les comptes désactivés", async () => {
    vue.avecInactifs = false;
    render(<UsersPage />);

    await userEvent.click(
      screen.getByRole("button", { name: "Afficher les inactifs" }),
    );

    expect(vue.basculerInactifs).toHaveBeenCalledTimes(1);
  });

  it("donne la dernière connexion de chacun", () => {
    render(<UsersPage />);

    expect(
      screen.getByRole("columnheader", { name: "Dernière connexion" }),
    ).toBeInTheDocument();
    expect(screen.getByText("il y a 3 h")).toBeInTheDocument();
    expect(screen.getByText("Jamais")).toBeInTheDocument();
  });

  it("nomme le statut de chaque compte", () => {
    vue.isManager = false;
    render(<UsersPage />);

    expect(screen.getAllByText("Actif")).toHaveLength(2);
  });

  it("laisse un manager couper l'accès d'un autre, jamais le sien", () => {
    // Se desactiver soi-meme, c'est s'enfermer dehors : l'API le refuse, et
    // l'ecran n'a pas a proposer un geste qui sera rejete.
    vue.isManager = true;
    vue.moiId = 1;
    render(<UsersPage />);

    const boutons = screen.getAllByRole("button", { name: "Désactiver ce compte" });
    expect(boutons).toHaveLength(1);
  });

  it("annonce une liste vide plutôt qu'un tableau sans ligne", () => {
    vue.collaborateurs = [];
    render(<UsersPage />);

    expect(screen.getByText(/Aucun user/)).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });
});
