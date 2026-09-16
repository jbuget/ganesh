import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { AppSidebar } from "./AppSidebar";

const pathname = vi.hoisted(() => ({ value: "/" }));
const utilisateur = vi.hoisted(() => ({
  value: { display_name: "Jérémy Buget", role: "MANAGER" } as
    { display_name: string; role: string } | undefined,
}));

vi.mock("next/navigation", () => ({ usePathname: () => pathname.value }));
vi.mock("@/lib/api/queries", () => ({
  useCurrentUser: () => ({ user: utilisateur.value }),
}));

describe("AppSidebar", () => {
  it("propose les deux écrans", () => {
    render(<AppSidebar />);

    expect(screen.getByRole("link", { name: /Activité/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Projets/ })).toBeInTheDocument();
  });

  it("signale l'écran courant aux lecteurs d'écran", () => {
    pathname.value = "/";
    render(<AppSidebar />);

    expect(screen.getByRole("link", { name: /Activité/ })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: /Projets/ })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("suit la page affichée", () => {
    pathname.value = "/projets";
    render(<AppSidebar />);

    expect(screen.getByRole("link", { name: /Projets/ })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("affiche l'utilisateur courant en bas", () => {
    render(<AppSidebar />);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
  });

  it("signale le rôle de manager", () => {
    utilisateur.value = { display_name: "Jérémy Buget", role: "MANAGER" };
    render(<AppSidebar />);

    expect(screen.getByText("Manager")).toBeInTheDocument();
  });

  it("n'affiche aucun rôle pour un collaborateur", () => {
    utilisateur.value = { display_name: "L. Chen", role: "TEAMMATE" };
    render(<AppSidebar />);

    expect(screen.queryByText("Manager")).toBeNull();
    expect(screen.getByText("L. Chen")).toBeInTheDocument();
  });

  it("réduit le nom à ses initiales dans la pastille", () => {
    utilisateur.value = { display_name: "Jérémy Buget", role: "TEAMMATE" };
    render(<AppSidebar />);

    expect(screen.getByText("JB")).toBeInTheDocument();
  });

  it("ne montre aucun bloc utilisateur tant que l'identité n'est pas connue", () => {
    utilisateur.value = undefined;
    render(<AppSidebar />);

    expect(screen.queryByText(/Buget|Chen/)).toBeNull();
  });
});
