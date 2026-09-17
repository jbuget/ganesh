import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { MissionRow } from "./MissionRow";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";

const MAINTENANT = new Date("2026-09-17T12:00:00Z");

const membre = (id: number, nom: string) => ({
  id,
  display_name: nom,
  initiales: nom.slice(0, 2).toUpperCase(),
});

const mission = (champs: Record<string, unknown> = {}): ProjectListItemResponse =>
  ({
    project: {
      id: 1,
      label: "Portail",
      kind: "projet",
      statut: "realisation",
      categorie: "automatiser_fluidifier",
      estime_j: 12,
      parent_id: null,
      actif: true,
      ...champs,
    },
    referents: [],
    intervenants: [],
    realise_j: 0,
    commentaires: 0,
    derniere_maj: null,
  }) as unknown as ProjectListItemResponse;

function ligne(contenu: React.ReactNode) {
  return render(
    <table>
      <tbody>{contenu}</tbody>
    </table>,
  );
}

describe("MissionRow", () => {
  it("affiche la phase, la catégorie et l'estimé", () => {
    ligne(
      <MissionRow
        mission={mission()}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.getByText("Réalisation")).toBeInTheDocument();
    expect(screen.getByText("Automatiser & fluidifier")).toBeInTheDocument();
    expect(screen.getByText("12 jrs.")).toBeInTheDocument();
  });

  it("porte la priorité déclarée", () => {
    ligne(
      <MissionRow
        mission={mission({ priorite: "critique" })}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.getByText("Critique")).toBeInTheDocument();
  });

  it("laisse la colonne vide quand la mission n'est pas située", () => {
    ligne(
      <MissionRow
        mission={mission({ priorite: null })}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    ["Critique", "Haute", "Normale", "Basse"].forEach((urgence) => {
      expect(screen.queryByText(urgence)).toBeNull();
    });
  });

  it("montre le réalisé à côté de l'estimé", () => {
    const consommee = {
      ...mission(),
      realise_j: 4.5,
    } as ProjectListItemResponse;

    ligne(
      <MissionRow
        mission={consommee}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.getByText("4.5 jrs.")).toBeInTheDocument();
  });

  it("laisse le réalisé vide tant que rien n'est déclaré", () => {
    ligne(
      <MissionRow
        mission={mission()}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.getAllByText(/jrs\./)).toHaveLength(1);
  });

  it("porte le décompte du fil de suivi de sa mission", () => {
    const suivie = { ...mission(), commentaires: 3 } as ProjectListItemResponse;

    ligne(
      <MissionRow
        mission={suivie}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.getByLabelText("3 mises à jour")).toHaveTextContent("3");
  });

  it("montre au survol le dernier message, signé, daté et mis en forme", () => {
    const suivie = {
      ...mission(),
      commentaires: 2,
      derniere_maj: {
        author: { id: 1, display_name: "Léa Chen", initiales: "LÉ" },
        texte: "La **recette** commence lundi",
        publiee_le: "2026-09-17T09:00:00Z",
      },
    } as ProjectListItemResponse;

    ligne(
      <MissionRow
        mission={suivie}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );
    fireEvent.mouseMove(screen.getByLabelText("2 mises à jour"));

    const infobulle = screen.getByRole("tooltip");
    expect(infobulle).toHaveTextContent("Léa Chen");
    expect(infobulle).toHaveTextContent("il y a 3 h");
    expect(infobulle).toHaveTextContent("La recette commence lundi");
    expect(infobulle.querySelector("strong")).toHaveTextContent("recette");
  });

  it("donne le message en entier, sans le tronquer", () => {
    const long = `${"mot ".repeat(200)}fin`;
    const suivie = {
      ...mission(),
      commentaires: 1,
      derniere_maj: {
        author: { id: 1, display_name: "Léa Chen", initiales: "LÉ" },
        texte: long,
        publiee_le: "2026-09-17T09:00:00Z",
      },
    } as ProjectListItemResponse;

    ligne(
      <MissionRow
        mission={suivie}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );
    fireEvent.mouseMove(screen.getByLabelText("1 mise à jour"));

    expect(screen.getByRole("tooltip")).toHaveTextContent("fin");
  });

  it("ouvre le fil de la mission au clic sur son décompte", () => {
    const ouvrirFil = vi.fn();
    const ouvrir = vi.fn();
    const suivie = { ...mission(), commentaires: 2 } as ProjectListItemResponse;

    ligne(
      <MissionRow
        mission={suivie}
        maintenant={MAINTENANT}
        onOpen={ouvrir}
        onOpenFil={ouvrirFil}
      />,
    );
    fireEvent.click(screen.getByLabelText("2 mises à jour"));

    expect(ouvrirFil).toHaveBeenCalledTimes(1);
    // La ligne entiere ouvre la mission : le decompte ne doit pas faire les deux.
    expect(ouvrir).not.toHaveBeenCalled();
  });

  it("n'affiche rien tant que le fil est vide", () => {
    ligne(
      <MissionRow
        mission={mission()}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.queryByLabelText(/mise/)).not.toBeInTheDocument();
  });

  it("ouvre la mission au clic sur son nom", () => {
    const ouvrir = vi.fn();
    ligne(
      <MissionRow
        mission={mission()}
        maintenant={MAINTENANT}
        onOpen={ouvrir}
        onOpenFil={() => {}}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Portail" }));

    expect(ouvrir).toHaveBeenCalledTimes(1);
  });

  it("distingue les référents des intervenants", () => {
    const avecMonde = {
      ...mission(),
      referents: [membre(1, "Léa Chen")],
      intervenants: [membre(2, "Nino Garo")],
    } as ProjectListItemResponse;

    ligne(
      <MissionRow
        mission={avecMonde}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.getByText("LÉ")).toBeInTheDocument();
    expect(screen.getByText("NI")).toBeInTheDocument();
  });

  it("laisse les colonnes vides plutôt que d'inventer une valeur", () => {
    ligne(
      <MissionRow
        mission={mission({ categorie: null, estime_j: null })}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.queryByText(/jrs\./)).not.toBeInTheDocument();
    expect(screen.getByText("Réalisation")).toBeInTheDocument();
  });

  it("rattache visuellement un sous-projet à son parent", () => {
    ligne(
      <MissionRow
        mission={mission()}
        estLot
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.getByText("\u2514")).toBeInTheDocument();
  });

  it("ne marque pas un projet de premier niveau", () => {
    ligne(
      <MissionRow
        mission={mission()}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.queryByText("\u2514")).not.toBeInTheDocument();
  });

  it("annonce une activité hors projet, qui n'a pas de phase", () => {
    ligne(
      <MissionRow
        mission={mission({ kind: "hors_projet", statut: null, estime_j: null })}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.queryByText("Réalisation")).not.toBeInTheDocument();
  });
});
