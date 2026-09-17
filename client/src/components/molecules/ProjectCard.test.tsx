import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { ProjectCard } from "./ProjectCard";
import type { BoardCardResponse } from "@/lib/api/generated/model";

/** Heure de reference figee : « il y a 2 h » doit rester stable d'un run a l'autre. */
const MAINTENANT = new Date("2026-09-16T11:00:00Z");

const card = (over: Record<string, unknown> = {}): BoardCardResponse =>
  ({
    consumed_days: 5,
    contributors: [{ id: 1, display_name: "Léa Chen", initials: "LC" }],
    comments: 0,
    latest_update: null,
    sub_projects: 0,
    parent: null,
    ...over,
    project: {
      id: 1,
      label: "Portail bailleurs",
      kind: "project",
      status: "build",
      parent_id: null,
      is_active: true,
      estimated_days: 20,
      category: "innovate_differentiate",
      go_live_date: "2026-11-15",
      position: 0,
      monday_item_id: null,
      monday_subitem_id: null,
      is_syncable_to_monday: false,
      is_deletable: false,
      ...(over.project as object),
    },
  }) as BoardCardResponse;

describe("ProjectCard", () => {
  it("affiche le nom de la mission", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card()} />);

    expect(screen.getByRole("heading")).toHaveTextContent("Portail bailleurs");
  });

  it("compare le consommé à l'estimé", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card()} />);

    expect(screen.getByText("5/20 jrs. estimés")).toBeInTheDocument();
  });

  it("écrit les demi-journées en décimal plutôt qu'en fraction", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card({ consumed_days: 7.5 })} />);

    expect(screen.getByText("7,5/20 jrs. estimés")).toBeInTheDocument();
  });

  it("se contente du consommé quand aucun estimé n'existe", () => {
    render(
      <ProjectCard
        maintenant={MAINTENANT}
        card={card({ project: { estimated_days: null } })}
      />,
    );

    expect(screen.getByText("5 jrs. consommés")).toBeInTheDocument();
  });

  it("ne charge pas la carte de la date de mise en service", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card()} />);

    expect(screen.queryByText(/Mise en service/)).toBeNull();
  });

  it("affiche les intervenants", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card()} />);

    expect(screen.getByText("LC")).toBeInTheDocument();
  });

  it("signale un dépassement du budget", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card({ consumed_days: 25 })} />);

    expect(screen.getByText("25/20 jrs. estimés").className).toContain("text-red-700");
  });

  it("alerte à l'approche du budget", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card({ consumed_days: 17 })} />);

    expect(screen.getByText("17/20 jrs. estimés").className).toContain(
      "text-amber-700",
    );
  });

  it("reste discret loin du budget", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card({ consumed_days: 3 })} />);

    expect(screen.getByText("3/20 jrs. estimés").className).not.toContain(
      "text-red-700",
    );
  });
});

describe("ce que la carte ne dit pas", () => {
  // Le tableau sert a piloter : ou en est une mission, ce qu'elle a coute, qui
  // s'en occupe. L'urgence et l'axe strategique se lisent dans la fiche et
  // dans le referentiel, qui sont faits pour comparer.
  it("laisse l'urgence et l'axe hors de la carte", () => {
    render(
      <ProjectCard
        maintenant={MAINTENANT}
        card={card({ project: { priority: "critical" } })}
      />,
    );

    expect(screen.queryByText("Critique")).toBeNull();
    expect(screen.queryByText("Innover & différencier")).toBeNull();
  });
});

describe("mission archivée", () => {
  it("se signale d'un coup d'œil", () => {
    render(
      <ProjectCard
        maintenant={MAINTENANT}
        card={card({ project: { is_active: false } })}
      />,
    );

    expect(screen.getByText("Archivée")).toBeInTheDocument();
  });

  it("ne marque rien sur une mission active", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card()} />);

    expect(screen.queryByText("Archivée")).toBeNull();
  });
});

describe("ce que la carte porte en pied", () => {
  it("compte les commentaires du fil de suivi", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card({ comments: 2 })} />);

    expect(screen.getByLabelText("2 commentaires")).toHaveTextContent("2");
  });

  it("accorde le libellé au singulier", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card({ comments: 1 })} />);

    expect(screen.getByLabelText("1 commentaire")).toBeInTheDocument();
  });

  it("compte les sous-projets", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card({ sub_projects: 11 })} />);

    expect(screen.getByLabelText("11 sous-projets")).toHaveTextContent("11");
  });

  it("garde les repères sans rien compter quand la mission est nue", () => {
    // Monday laisse les icones en place, sans nombre : la carte garde sa forme
    // d'une mission a l'autre, et l'absence se lit aussi vite qu'un total.
    render(<ProjectCard maintenant={MAINTENANT} card={card()} />);

    expect(screen.getByLabelText("Aucun commentaire")).toHaveTextContent("");
    expect(screen.getByLabelText("Aucun sous-projet")).toHaveTextContent("");
  });
});

describe("rattachement à un projet parent", () => {
  it("nomme le projet dont le sous-projet relève", () => {
    render(
      <ProjectCard
        maintenant={MAINTENANT}
        card={card({ parent: { id: 7, label: "Refonte du SI" } })}
      />,
    );

    expect(screen.getByText("Refonte du SI")).toBeInTheDocument();
  });

  it("ouvre le parent sans ouvrir la mission elle-même", () => {
    const onOpen = vi.fn();
    render(
      <ProjectCard
        maintenant={MAINTENANT}
        card={card({ parent: { id: 7, label: "Refonte du SI" } })}
        onOpen={onOpen}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Refonte du SI" }));

    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(onOpen).toHaveBeenCalledWith(7);
  });

  it("ne montre aucun parent à un projet racine", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card()} />);

    expect(screen.queryByText(/↳/)).toBeNull();
  });

  it("fige le lien pendant le glissement", () => {
    // La copie qui suit le curseur represente un geste en cours : un lien
    // cliquable dessus n'aurait aucune cible.
    render(
      <ProjectCard
        maintenant={MAINTENANT}
        card={card({ parent: { id: 7, label: "Refonte du SI" } })}
        onOpen={vi.fn()}
        isDragging
      />,
    );

    expect(screen.queryByRole("button", { name: "Refonte du SI" })).toBeNull();
    expect(screen.getByText("Refonte du SI")).toBeInTheDocument();
  });
});

describe("ouverture de la mission", () => {
  it("ouvre la mission au clic n'importe où sur la carte", () => {
    const onOpen = vi.fn();
    render(<ProjectCard maintenant={MAINTENANT} card={card()} onOpen={onOpen} />);

    fireEvent.click(screen.getByText("5/20 jrs. estimés"));

    expect(onOpen).toHaveBeenCalledWith(1);
  });

  it("ouvre aussi depuis le titre, atteignable au clavier", () => {
    const onOpen = vi.fn();
    render(<ProjectCard maintenant={MAINTENANT} card={card()} onOpen={onOpen} />);

    fireEvent.click(screen.getByRole("button", { name: "Portail bailleurs" }));

    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("laisse leur clic aux contrôles que la carte porte", () => {
    // La poignee de glissement et les pastilles d'intervenants ne doivent pas
    // ouvrir la mission sous le doigt de celui qui les visait.
    const onOpen = vi.fn();
    render(
      <ProjectCard
        maintenant={MAINTENANT}
        card={card()}
        onOpen={onOpen}
        handle={<button aria-label="Déplacer">glisser</button>}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Déplacer" }));

    expect(onOpen).not.toHaveBeenCalled();
  });

  it("ne montre aucune poignée quand la carte ne se déplace pas", () => {
    const { rerender } = render(<ProjectCard maintenant={MAINTENANT} card={card()} />);
    expect(document.querySelector("svg.lucide-grip-vertical")).not.toBeNull();

    rerender(<ProjectCard maintenant={MAINTENANT} card={card()} handle={null} />);

    expect(document.querySelector("svg.lucide-grip-vertical")).toBeNull();
  });

  it("n'ouvre rien quand la carte suit le curseur", () => {
    // La copie qui suit la souris represente un geste en cours, pas une cible.
    const onOpen = vi.fn();
    render(
      <ProjectCard maintenant={MAINTENANT} card={card()} onOpen={onOpen} isDragging />,
    );

    fireEvent.click(screen.getByText("5/20 jrs. estimés"));

    expect(onOpen).not.toHaveBeenCalled();
  });

  it("montre le dernier message au survol du décompte de commentaires", () => {
    render(
      <ProjectCard
        maintenant={MAINTENANT}
        card={card({
          comments: 2,
          latest_update: {
            author: { id: 1, display_name: "J. Buget", initials: "JB" },
            body: "Le cadrage commence lundi",
            published_at: "2026-09-16T09:00:00Z",
          },
        })}
      />,
    );

    fireEvent.mouseMove(screen.getByLabelText("2 commentaires"));

    const apercu = screen.getByRole("tooltip");
    expect(apercu).toHaveTextContent("J. Buget");
    expect(apercu).toHaveTextContent("il y a 2 h");
    expect(apercu).toHaveTextContent("Le cadrage commence lundi");
  });

  it("ne montre aucun aperçu quand le fil est vide", () => {
    render(<ProjectCard maintenant={MAINTENANT} card={card({ comments: 0 })} />);

    fireEvent.mouseMove(screen.getByLabelText("Aucun commentaire"));

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
