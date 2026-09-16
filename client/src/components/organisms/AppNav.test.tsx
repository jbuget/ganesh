import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { AppNav } from "./AppNav";

const pathname = vi.hoisted(() => ({ value: "/" }));
vi.mock("next/navigation", () => ({ usePathname: () => pathname.value }));

describe("AppNav", () => {
  it("propose les deux écrans", () => {
    render(<AppNav />);

    expect(screen.getByRole("link", { name: "Activité" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Projets" })).toBeInTheDocument();
  });

  it("signale l'écran courant aux lecteurs d'écran", () => {
    pathname.value = "/";
    render(<AppNav />);

    expect(screen.getByRole("link", { name: "Activité" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Projets" })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("suit la page affichée", () => {
    pathname.value = "/projets";
    render(<AppNav />);

    expect(screen.getByRole("link", { name: "Projets" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });
});
