import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

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
    intervenants: [{ id: 1, display_name: "Léa Chen", initiales: "LC" }],
    commentaires: 0,
    sous_projets: 0,
    parent: null,
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

  it("écrit les demi-journées en décimal plutôt qu'en fraction", () => {
    render(<ProjectCard carte={carte({ consomme_j: 7.5 })} />);

    expect(screen.getByText("7,5/20 jrs. estimés")).toBeInTheDocument();
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

describe("ce que la carte porte en pied", () => {
  it("compte les commentaires du fil de suivi", () => {
    render(<ProjectCard carte={carte({ commentaires: 2 })} />);

    expect(screen.getByLabelText("2 commentaires")).toHaveTextContent("2");
  });

  it("accorde le libellé au singulier", () => {
    render(<ProjectCard carte={carte({ commentaires: 1 })} />);

    expect(screen.getByLabelText("1 commentaire")).toBeInTheDocument();
  });

  it("compte les sous-projets", () => {
    render(<ProjectCard carte={carte({ sous_projets: 11 })} />);

    expect(screen.getByLabelText("11 sous-projets")).toHaveTextContent("11");
  });

  it("garde les repères sans rien compter quand la mission est nue", () => {
    // Monday laisse les icones en place, sans nombre : la carte garde sa forme
    // d'une mission a l'autre, et l'absence se lit aussi vite qu'un total.
    render(<ProjectCard carte={carte()} />);

    expect(screen.getByLabelText("Aucun commentaire")).toHaveTextContent("");
    expect(screen.getByLabelText("Aucun sous-projet")).toHaveTextContent("");
  });
});

describe("rattachement à un projet parent", () => {
  it("nomme le projet dont le sous-projet relève", () => {
    render(
      <ProjectCard carte={carte({ parent: { id: 7, label: "Refonte du SI" } })} />,
    );

    expect(screen.getByText("Refonte du SI")).toBeInTheDocument();
  });

  it("ouvre le parent sans ouvrir la mission elle-même", () => {
    const onOpen = vi.fn();
    render(
      <ProjectCard
        carte={carte({ parent: { id: 7, label: "Refonte du SI" } })}
        onOpen={onOpen}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Refonte du SI" }));

    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(onOpen).toHaveBeenCalledWith(7);
  });

  it("ne montre aucun parent à un projet racine", () => {
    render(<ProjectCard carte={carte()} />);

    expect(screen.queryByText(/↳/)).toBeNull();
  });

  it("fige le lien pendant le glissement", () => {
    // La copie qui suit le curseur represente un geste en cours : un lien
    // cliquable dessus n'aurait aucune cible.
    render(
      <ProjectCard
        carte={carte({ parent: { id: 7, label: "Refonte du SI" } })}
        onOpen={vi.fn()}
        enDeplacement
      />,
    );

    expect(screen.queryByRole("button", { name: "Refonte du SI" })).toBeNull();
    expect(screen.getByText("Refonte du SI")).toBeInTheDocument();
  });
});

describe("ouverture de la mission", () => {
  it("ouvre la mission au clic n'importe où sur la carte", () => {
    const onOpen = vi.fn();
    render(<ProjectCard carte={carte()} onOpen={onOpen} />);

    fireEvent.click(screen.getByText("5/20 jrs. estimés"));

    expect(onOpen).toHaveBeenCalledWith(1);
  });

  it("ouvre aussi depuis le titre, atteignable au clavier", () => {
    const onOpen = vi.fn();
    render(<ProjectCard carte={carte()} onOpen={onOpen} />);

    fireEvent.click(screen.getByRole("button", { name: "Portail bailleurs" }));

    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("laisse leur clic aux contrôles que la carte porte", () => {
    // La poignee de glissement et les pastilles d'intervenants ne doivent pas
    // ouvrir la mission sous le doigt de celui qui les visait.
    const onOpen = vi.fn();
    render(
      <ProjectCard
        carte={carte()}
        onOpen={onOpen}
        poignee={<button aria-label="Déplacer">glisser</button>}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Déplacer" }));

    expect(onOpen).not.toHaveBeenCalled();
  });

  it("ne montre aucune poignée quand la carte ne se déplace pas", () => {
    const { rerender } = render(<ProjectCard carte={carte()} />);
    expect(document.querySelector("svg.lucide-grip-vertical")).not.toBeNull();

    rerender(<ProjectCard carte={carte()} poignee={null} />);

    expect(document.querySelector("svg.lucide-grip-vertical")).toBeNull();
  });

  it("n'ouvre rien quand la carte suit le curseur", () => {
    // La copie qui suit la souris represente un geste en cours, pas une cible.
    const onOpen = vi.fn();
    render(<ProjectCard carte={carte()} onOpen={onOpen} enDeplacement />);

    fireEvent.click(screen.getByText("5/20 jrs. estimés"));

    expect(onOpen).not.toHaveBeenCalled();
  });
});
