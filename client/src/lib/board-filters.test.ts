import { describe, expect, it } from "vitest";

import {
  AUCUN_FILTRE,
  ecrireFiltres,
  filtreActif,
  filtrerCartes,
  lireFiltres,
  type BoardFilters,
} from "./board-filters";
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
      date_mise_en_service: null,
      position: 0,
      monday_item_id: null,
      monday_subitem_id: null,
      is_syncable_to_monday: false,
      is_deletable: false,
      ...(over.project as object),
    },
    consomme_j: 0,
    intervenants: [{ id: 1, display_name: "Léa Chen", initiales: "LC" }],
    commentaires: 0,
    sous_projets: 0,
    parent: null,
    ...over,
  }) as BoardCardResponse;

const filtres = (over: Partial<BoardFilters> = {}): BoardFilters => ({
  ...AUCUN_FILTRE,
  ...over,
});

describe("filtreActif", () => {
  it("ne voit aucun filtre sur des critères vides", () => {
    expect(filtreActif(AUCUN_FILTRE)).toBe(false);
  });

  it("ignore un nom fait d'espaces", () => {
    expect(filtreActif(filtres({ nom: "   " }))).toBe(false);
  });

  it("se déclenche dès qu'un critère est posé", () => {
    expect(filtreActif(filtres({ phases: ["cadrage"] }))).toBe(true);
    expect(filtreActif(filtres({ nom: "portail" }))).toBe(true);
  });
});

describe("recherche par nom", () => {
  it("retient une mission dont le nom contient la recherche", () => {
    expect(filtrerCartes([carte()], filtres({ nom: "bailleurs" }))).toHaveLength(1);
  });

  it("ignore la casse et les accents", () => {
    const cartes = [carte({ project: { label: "Refonte extranet copropriété" } })];

    expect(filtrerCartes(cartes, filtres({ nom: "COPROPRIETE" }))).toHaveLength(1);
  });

  it("écarte ce qui ne correspond pas", () => {
    expect(filtrerCartes([carte()], filtres({ nom: "facturation" }))).toHaveLength(0);
  });
});

describe("critères à choix multiples", () => {
  it("retient les missions de l'une des catégories choisies", () => {
    const cartes = [
      carte({ project: { id: 1, categorie: "innover_differencier" } }),
      carte({ project: { id: 2, categorie: "structurer_plateforme" } }),
      carte({ project: { id: 3, categorie: null } }),
    ];

    const retenues = filtrerCartes(
      cartes,
      filtres({ categories: ["innover_differencier", "structurer_plateforme"] }),
    );

    expect(retenues.map((c) => c.project.id)).toEqual([1, 2]);
  });

  it("retient les missions portées par l'un des intervenants choisis", () => {
    const cartes = [
      carte({ project: { id: 1 }, intervenants: [{ id: 7 } as never] }),
      carte({ project: { id: 2 }, intervenants: [] }),
    ];

    const retenues = filtrerCartes(cartes, filtres({ intervenants: [7] }));

    expect(retenues.map((c) => c.project.id)).toEqual([1]);
  });

  it("distingue les projets de leurs sous-projets", () => {
    const cartes = [
      carte({ project: { id: 1, kind: "projet" } }),
      carte({ project: { id: 2, kind: "lot", parent_id: 1 } }),
    ];

    expect(
      filtrerCartes(cartes, filtres({ types: ["lot"] })).map((c) => c.project.id),
    ).toEqual([2]);
    expect(filtrerCartes(cartes, filtres({ types: ["projet", "lot"] }))).toHaveLength(
      2,
    );
  });

  it("combine les critères : tous doivent être satisfaits", () => {
    const cartes = [
      carte({
        project: { id: 1, label: "Portail", categorie: "innover_differencier" },
      }),
      carte({
        project: { id: 2, label: "Portail", categorie: "structurer_plateforme" },
      }),
    ];

    const retenues = filtrerCartes(
      cartes,
      filtres({ nom: "portail", categories: ["structurer_plateforme"] }),
    );

    expect(retenues.map((c) => c.project.id)).toEqual([2]);
  });
});

describe("filtrage par phase", () => {
  const cartes = [
    carte({ project: { id: 1, statut: "realisation" } }),
    carte({ project: { id: 2, statut: "cadrage" } }),
  ];

  it("garde toutes les missions quand aucune phase n'est choisie", () => {
    expect(filtrerCartes(cartes, AUCUN_FILTRE)).toHaveLength(2);
  });

  it("ne garde que les missions des phases choisies", () => {
    const retenues = filtrerCartes(cartes, filtres({ phases: ["realisation"] }));

    expect(retenues.map((c) => c.project.id)).toEqual([1]);
  });
});

describe("filtres portés par l'URL", () => {
  it("relit ce qu'il a écrit", () => {
    const choisis = filtres({
      nom: "portail",
      phases: ["cadrage", "realisation"],
      categories: ["innover_differencier"],
      intervenants: [3, 7],
      types: ["lot"],
    });

    const params = new URLSearchParams();
    ecrireFiltres(params, choisis);

    expect(lireFiltres(params)).toEqual(choisis);
  });

  it("n'écrit rien quand aucun filtre n'est posé", () => {
    const params = new URLSearchParams("mission=12");
    ecrireFiltres(params, AUCUN_FILTRE);

    expect(params.toString()).toBe("mission=12");
  });

  it("laisse les autres paramètres en place", () => {
    const params = new URLSearchParams("mission=12&phase=cadrage");
    ecrireFiltres(params, filtres({ phases: ["realisation"] }));

    expect(params.get("mission")).toBe("12");
    expect(params.getAll("phase")).toEqual(["realisation"]);
  });

  it("ignore une valeur inconnue plutôt que de vider l'écran", () => {
    const params = new URLSearchParams("phase=sieste&intervenant=abc");

    expect(lireFiltres(params)).toEqual(AUCUN_FILTRE);
  });
});
