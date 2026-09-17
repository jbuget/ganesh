import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ProjectCard } from "./ProjectCard";
import type { BoardCardResponse } from "@/lib/api/generated/model";

const carte = (over: Record<string, unknown> = {}): BoardCardResponse =>
  ({
    project: {
      id: 1,
      label: "Portail bailleurs",
      kind: "projet",
      statut: "realisation",
      parent_id: null,
      actif: true,
      estime_j: 20,
      categorie: "innover_differencier",
      date_mise_en_service: "2026-11-15",
      position: 0,
      monday_item_id: null,
      monday_subitem_id: null,
      is_syncable_to_monday: false,
      is_deletable: false,
      ...(over.project as object),
    },
    consomme_j: 5,
    collaborateurs: [{ id: 1, display_name: "Léa Chen", initiales: "LC" }],
    ...over,
  }) as BoardCardResponse;

describe("ProjectCard", () => {
  it("affiche le nom de la mission", () => {
    render(<ProjectCard carte={carte()} />);

    expect(screen.getByRole("heading")).toHaveTextContent("Portail bailleurs");
  });

  it("affiche l'axe stratégique", () => {
    render(<ProjectCard carte={carte()} />);

    expect(screen.getByText("Innover & différencier")).toBeInTheDocument();
  });

  it("compare le consommé à l'estimé", () => {
    render(<ProjectCard carte={carte()} />);

    expect(screen.getByText("5/20 jrs. estimés")).toBeInTheDocument();
  });

  it("se contente du consommé quand aucun estimé n'existe", () => {
    render(<ProjectCard carte={carte({ project: { estime_j: null } })} />);

    expect(screen.getByText("5 jrs. consommés")).toBeInTheDocument();
  });

  it("ne charge pas la carte de la date de mise en service", () => {
    render(<ProjectCard carte={carte()} />);

    expect(screen.queryByText(/Mise en service/)).toBeNull();
  });

  it("affiche les intervenants", () => {
    render(<ProjectCard carte={carte()} />);

    expect(screen.getByText("LC")).toBeInTheDocument();
  });

  it("signale un dépassement du budget", () => {
    render(<ProjectCard carte={carte({ consomme_j: 25 })} />);

    expect(screen.getByText("25/20 jrs. estimés").className).toContain("text-red-700");
  });

  it("alerte à l'approche du budget", () => {
    render(<ProjectCard carte={carte({ consomme_j: 17 })} />);

    expect(screen.getByText("17/20 jrs. estimés").className).toContain(
      "text-amber-700",
    );
  });

  it("reste discret loin du budget", () => {
    render(<ProjectCard carte={carte({ consomme_j: 3 })} />);

    expect(screen.getByText("3/20 jrs. estimés").className).not.toContain(
      "text-red-700",
    );
  });
});
