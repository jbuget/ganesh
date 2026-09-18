import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { MissionRow } from "./MissionRow";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";

const MAINTENANT = new Date("2026-09-17T12:00:00Z");

const member = (id: number, name: string) => ({
  id,
  display_name: name,
  initials: name.slice(0, 2).toUpperCase(),
});

const mission = (champs: Record<string, unknown> = {}): ProjectListItemResponse =>
  ({
    project: {
      id: 1,
      label: "Portail",
      kind: "project",
      status: "development",
      category: "automate_streamline",
      estimated_days: 12,
      parent_id: null,
      is_active: true,
      ...champs,
    },
    leads: [],
    contributors: [],
    delivered_days: 0,
    comments: 0,
    latest_update: null,
  }) as unknown as ProjectListItemResponse;

function line(content: React.ReactNode) {
  return render(
    <table>
      <tbody>{content}</tbody>
    </table>,
  );
}

describe("MissionRow", () => {
  it("affiche la phase, la catégorie et l'estimé", () => {
    line(
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
    line(
      <MissionRow
        mission={mission({ priority: "critical" })}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.getByText("Critique")).toBeInTheDocument();
  });

  it("laisse la colonne vide quand la mission n'est pas située", () => {
    line(
      <MissionRow
        mission={mission({ priority: null })}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    ["Critique", "Haute", "Normale", "Basse"].forEach((urgency) => {
      expect(screen.queryByText(urgency)).toBeNull();
    });
  });

  it("montre le réalisé à côté de l'estimé", () => {
    const consommee = {
      ...mission(),
      delivered_days: 4.5,
    } as ProjectListItemResponse;

    line(
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
    line(
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
    const suivie = { ...mission(), comments: 3 } as ProjectListItemResponse;

    line(
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
      comments: 2,
      latest_update: {
        author: { id: 1, display_name: "Léa Chen", initials: "LÉ" },
        body: "La **recette** commence lundi",
        published_at: "2026-09-17T09:00:00Z",
      },
    } as ProjectListItemResponse;

    line(
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
      comments: 1,
      latest_update: {
        author: { id: 1, display_name: "Léa Chen", initials: "LÉ" },
        body: long,
        published_at: "2026-09-17T09:00:00Z",
      },
    } as ProjectListItemResponse;

    line(
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
    const open = vi.fn();
    const suivie = { ...mission(), comments: 2 } as ProjectListItemResponse;

    line(
      <MissionRow
        mission={suivie}
        maintenant={MAINTENANT}
        onOpen={open}
        onOpenFil={ouvrirFil}
      />,
    );
    fireEvent.click(screen.getByLabelText("2 mises à jour"));

    expect(ouvrirFil).toHaveBeenCalledTimes(1);
    // The whole row opens the mission: the counter must not do both.
    expect(open).not.toHaveBeenCalled();
  });

  it("n'affiche rien tant que le fil est vide", () => {
    line(
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
    const open = vi.fn();
    line(
      <MissionRow
        mission={mission()}
        maintenant={MAINTENANT}
        onOpen={open}
        onOpenFil={() => {}}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Portail" }));

    expect(open).toHaveBeenCalledTimes(1);
  });

  it("distingue les référents des intervenants", () => {
    const avecMonde = {
      ...mission(),
      leads: [member(1, "Léa Chen")],
      contributors: [member(2, "Nino Garo")],
    } as ProjectListItemResponse;

    line(
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
    line(
      <MissionRow
        mission={mission({ category: null, estimated_days: null })}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.queryByText(/jrs\./)).not.toBeInTheDocument();
    expect(screen.getByText("Réalisation")).toBeInTheDocument();
  });

  it("rattache visuellement un sous-projet à son parent", () => {
    line(
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
    line(
      <MissionRow
        mission={mission()}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.queryByText("\u2514")).not.toBeInTheDocument();
  });

  it("propose de replier un projet qui porte des sous-projets", () => {
    line(
      <MissionRow
        mission={mission()}
        lots={2}
        deplie
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
        onBasculer={() => {}}
      />,
    );

    const bascule = screen.getByRole("button", {
      name: "Masquer les 2 sous-projets de Portail",
    });
    expect(bascule).toHaveAttribute("aria-expanded", "true");
  });

  it("propose de déplier un projet dont les sous-projets sont cachés", () => {
    line(
      <MissionRow
        mission={mission()}
        lots={2}
        deplie={false}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
        onBasculer={() => {}}
      />,
    );

    const bascule = screen.getByRole("button", {
      name: "Afficher les 2 sous-projets de Portail",
    });
    expect(bascule).toHaveAttribute("aria-expanded", "false");
  });

  it("bascule les sous-projets sans ouvrir la mission", () => {
    const toggle = vi.fn();
    const open = vi.fn();

    line(
      <MissionRow
        mission={mission()}
        lots={1}
        deplie
        maintenant={MAINTENANT}
        onOpen={open}
        onOpenFil={() => {}}
        onBasculer={toggle}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Masquer le sous-projet de Portail" }),
    );

    expect(toggle).toHaveBeenCalledTimes(1);
    expect(open).not.toHaveBeenCalled();
  });

  it("n'offre aucune bascule à un projet sans sous-projet", () => {
    line(
      <MissionRow
        mission={mission()}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(
      screen.queryByRole("button", { name: /sous-projet/ }),
    ).not.toBeInTheDocument();
  });

  it("annonce une activité hors projet, qui n'a pas de phase", () => {
    line(
      <MissionRow
        mission={mission({ kind: "off_project", status: null, estimated_days: null })}
        maintenant={MAINTENANT}
        onOpen={() => {}}
        onOpenFil={() => {}}
      />,
    );

    expect(screen.queryByText("Réalisation")).not.toBeInTheDocument();
  });
});
