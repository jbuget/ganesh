import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { UserMenu } from "./UserMenu";
import type { UserResponse } from "@/lib/api/generated/model";

/**
 * Le menu repose sur le Popover de Base UI, qui ne s'ouvre pas sous jsdom : son
 * contenu — nom complet, adresse, role, deconnexion — se verifie dans le
 * navigateur. Ce qui suit couvre ce que la barre laterale montre en permanence.
 */
const USER: UserResponse = {
  id: 1,
  email: "j.buget@waat.fr",
  display_name: "Jérémy Buget",
  initiales: "JB",
  role: "MANAGER",
  actif: true,
} as UserResponse;

describe("UserMenu", () => {
  it("montre le nom et les initiales de la personne connectée", () => {
    render(<UserMenu user={USER} onSignOut={vi.fn()} />);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("JB")).toBeInTheDocument();
  });

  it("annonce ce que le menu ouvre", () => {
    render(<UserMenu user={USER} onSignOut={vi.fn()} />);

    expect(screen.getByRole("button", { name: /Jérémy Buget/ })).toBeInTheDocument();
  });

  it("signale le rôle de manager sous le nom", () => {
    render(<UserMenu user={USER} onSignOut={vi.fn()} />);

    expect(screen.getByText("Manager")).toBeInTheDocument();
  });

  it("n'affiche aucun rôle sous le nom d'un collaborateur", () => {
    render(<UserMenu user={{ ...USER, role: "TEAMMATE" }} onSignOut={vi.fn()} />);

    expect(screen.queryByText("Collaborateur")).toBeNull();
  });

  it("réduit le bloc aux initiales quand la barre est repliée", () => {
    render(<UserMenu user={USER} onSignOut={vi.fn()} repliee />);

    // Le nom quitte l'oeil, jamais l'arbre d'accessibilite.
    expect(screen.getByRole("button", { name: /Jérémy Buget/ })).toBeInTheDocument();
    expect(screen.getByText("JB")).toBeInTheDocument();
  });
});
