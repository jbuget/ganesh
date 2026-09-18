import { describe, expect, it } from "vitest";

import {
  NO_FILTER,
  ecrireFiltres,
  filtreActif,
  filtrerMissions,
  inclutLesArchivees,
  lireFiltres,
  type MissionFilters,
} from "./mission-filters";
import type { BoardCardResponse } from "@/lib/api/generated/model";

const card = (over: Record<string, unknown> = {}): BoardCardResponse =>
  ({
    consumed_days: 0,
    contributors: [{ id: 1, display_name: "Léa Chen", initials: "LC" }],
    comments: 0,
    sub_projects: 0,
    parent: null,
    ...over,
    project: {
      id: 1,
      label: "Portail bailleurs",
      kind: "project",
      status: "development",
      parent_id: null,
      is_active: true,
      estimated_days: 20,
      category: "innovate_differentiate",
      go_live_date: null,
      position: 0,
      monday_item_id: null,
      monday_subitem_id: null,
      is_syncable_to_monday: false,
      is_deletable: false,
      ...(over.project as object),
    },
  }) as BoardCardResponse;

const filters = (over: Partial<MissionFilters> = {}): MissionFilters => ({
  ...NO_FILTER,
  ...over,
});

describe("filtreActif", () => {
  it("ne voit aucun filtre sur des critères vides", () => {
    expect(filtreActif(NO_FILTER)).toBe(false);
  });

  it("ignore un nom fait d'espaces", () => {
    expect(filtreActif(filters({ name: "   " }))).toBe(false);
  });

  it("se déclenche dès qu'un critère est posé", () => {
    expect(filtreActif(filters({ phases: ["scoping"] }))).toBe(true);
    expect(filtreActif(filters({ name: "portail" }))).toBe(true);
  });
});

describe("recherche par nom", () => {
  it("retient une mission dont le nom contient la recherche", () => {
    expect(filtrerMissions([card()], filters({ name: "bailleurs" }))).toHaveLength(1);
  });

  it("ignore la casse et les accents", () => {
    const cards = [card({ project: { label: "Refonte extranet copropriété" } })];

    expect(filtrerMissions(cards, filters({ name: "COPROPRIETE" }))).toHaveLength(1);
  });

  it("écarte ce qui ne correspond pas", () => {
    expect(filtrerMissions([card()], filters({ name: "facturation" }))).toHaveLength(0);
  });
});

describe("critères à choix multiples", () => {
  it("retient les missions de l'une des catégories choisies", () => {
    const cards = [
      card({ project: { id: 1, category: "innovate_differentiate" } }),
      card({ project: { id: 2, category: "structure_platform" } }),
      card({ project: { id: 3, category: null } }),
    ];

    const kept = filtrerMissions(
      cards,
      filters({ categories: ["innovate_differentiate", "structure_platform"] }),
    );

    expect(kept.map((c) => c.project.id)).toEqual([1, 2]);
  });

  it("retient les missions de l'une des priorités choisies", () => {
    const cards = [
      card({ project: { id: 1, priority: "critical" } }),
      card({ project: { id: 2, priority: "low" } }),
      card({ project: { id: 3, priority: null } }),
    ];

    const kept = filtrerMissions(cards, filters({ priorities: ["critical"] }));

    expect(kept.map((c) => c.project.id)).toEqual([1]);
  });

  it("retient les missions portées par l'un des intervenants choisis", () => {
    const cards = [
      card({ project: { id: 1 }, contributors: [{ id: 7 } as never] }),
      card({ project: { id: 2 }, contributors: [] }),
    ];

    const kept = filtrerMissions(cards, filters({ contributors: [7] }));

    expect(kept.map((c) => c.project.id)).toEqual([1]);
  });

  it("distingue les projets de leurs sous-projets", () => {
    const cards = [
      card({ project: { id: 1, kind: "project" } }),
      card({ project: { id: 2, kind: "work_package", parent_id: 1 } }),
    ];

    expect(
      filtrerMissions(cards, filters({ types: ["work_package"] })).map(
        (c) => c.project.id,
      ),
    ).toEqual([2]);
    expect(
      filtrerMissions(cards, filters({ types: ["project", "work_package"] })),
    ).toHaveLength(2);
  });

  it("combine les critères : tous doivent être satisfaits", () => {
    const cards = [
      card({
        project: { id: 1, label: "Portail", category: "innovate_differentiate" },
      }),
      card({
        project: { id: 2, label: "Portail", category: "structure_platform" },
      }),
    ];

    const kept = filtrerMissions(
      cards,
      filters({ name: "portail", categories: ["structure_platform"] }),
    );

    expect(kept.map((c) => c.project.id)).toEqual([2]);
  });
});

describe("missions archivées", () => {
  const cards = [
    card({ project: { id: 1, is_active: true } }),
    card({ project: { id: 2, is_active: false } }),
  ];

  it("les écarte tant qu'on ne les demande pas", () => {
    const kept = filtrerMissions(cards, NO_FILTER);

    expect(kept.map((c) => c.project.id)).toEqual([1]);
  });

  it("ne montre qu'elles quand on ne demande qu'elles", () => {
    const kept = filtrerMissions(cards, filters({ states: ["archivee"] }));

    expect(kept.map((c) => c.project.id)).toEqual([2]);
  });

  it("montre les deux quand les deux états sont cochés", () => {
    const kept = filtrerMissions(cards, filters({ states: ["active", "archivee"] }));

    expect(kept.map((c) => c.project.id)).toEqual([1, 2]);
  });

  it("ne les redemande au serveur que si elles sont voulues", () => {
    expect(inclutLesArchivees(NO_FILTER)).toBe(false);
    expect(inclutLesArchivees(filters({ states: ["active"] }))).toBe(false);
    expect(inclutLesArchivees(filters({ states: ["archivee"] }))).toBe(true);
  });

  it("compte comme un filtre : le tableau n'est plus la vue de pilotage", () => {
    expect(filtreActif(filters({ states: ["archivee"] }))).toBe(true);
  });
});

describe("filtrage par phase", () => {
  const cards = [
    card({ project: { id: 1, status: "development" } }),
    card({ project: { id: 2, status: "scoping" } }),
  ];

  it("garde toutes les missions quand aucune phase n'est choisie", () => {
    expect(filtrerMissions(cards, NO_FILTER)).toHaveLength(2);
  });

  it("ne garde que les missions des phases choisies", () => {
    const kept = filtrerMissions(cards, filters({ phases: ["development"] }));

    expect(kept.map((c) => c.project.id)).toEqual([1]);
  });
});

describe("filtres portés par l'URL", () => {
  it("relit ce qu'il a écrit", () => {
    const chosen = filters({
      name: "portail",
      phases: ["scoping", "development"],
      categories: ["innovate_differentiate"],
      priorities: ["high"],
      contributors: [3, 7],
      types: ["work_package"],
      states: ["archivee"],
    });

    const params = new URLSearchParams();
    ecrireFiltres(params, chosen);

    expect(lireFiltres(params)).toEqual(chosen);
  });

  it("n'écrit rien quand aucun filtre n'est posé", () => {
    const params = new URLSearchParams("mission=12");
    ecrireFiltres(params, NO_FILTER);

    expect(params.toString()).toBe("mission=12");
  });

  it("laisse les autres paramètres en place", () => {
    const params = new URLSearchParams("mission=12&phase=scoping");
    ecrireFiltres(params, filters({ phases: ["development"] }));

    expect(params.get("mission")).toBe("12");
    expect(params.getAll("phase")).toEqual(["development"]);
  });

  it("ignore une valeur inconnue plutôt que de vider l'écran", () => {
    const params = new URLSearchParams("phase=sieste&contributor=abc");

    expect(lireFiltres(params)).toEqual(NO_FILTER);
  });
});
