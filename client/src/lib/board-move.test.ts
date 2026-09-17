import { describe, expect, it } from "vitest";

import { changerDeColonne, indexVise, localiser, reordonner } from "./board-move";
import type { BoardCardResponse, ProjectStatus } from "@/lib/api/generated/model";
import type { Colonnes } from "@/lib/use-board";
import { PHASES } from "@/lib/board";

const carte = (id: number): BoardCardResponse =>
  ({
    project: { id, label: `Mission ${id}` },
    consomme_j: 0,
    collaborateurs: [],
  }) as unknown as BoardCardResponse;

/** Colonnes vides, completees par celles qu'un test decrit. */
const colonnes = (garnies: Partial<Record<ProjectStatus, number[]>>): Colonnes =>
  Object.fromEntries(
    PHASES.map(({ statut }) => [statut, (garnies[statut] ?? []).map(carte)]),
  ) as Colonnes;

const ids = (cartes: BoardCardResponse[]) => cartes.map((c) => c.project.id);

describe("localiser", () => {
  it("rend la phase et le rang d'une carte", () => {
    const etat = colonnes({ cadrage: [1, 2], realisation: [3] });

    expect(localiser(etat, 2)).toEqual({ statut: "cadrage", position: 1 });
    expect(localiser(etat, 3)).toEqual({ statut: "realisation", position: 0 });
  });

  it("rend null pour une carte absente du tableau", () => {
    expect(localiser(colonnes({ cadrage: [1] }), 99)).toBeNull();
  });
});

describe("indexVise", () => {
  it("insère avant la carte survolée", () => {
    expect(indexVise(colonnes({ cadrage: [1, 2, 3] }).cadrage, 2, false)).toBe(1);
  });

  it("insère après la carte survolée quand on la dépasse", () => {
    expect(indexVise(colonnes({ cadrage: [1, 2, 3] }).cadrage, 2, true)).toBe(2);
  });

  it("vise la fin quand aucune carte n'est survolée", () => {
    expect(indexVise(colonnes({ cadrage: [1, 2, 3] }).cadrage, null, false)).toBe(3);
  });
});

describe("changerDeColonne", () => {
  it("retire la carte de sa phase et l'insère dans la nouvelle", () => {
    const etat = colonnes({ cadrage: [1, 2], realisation: [3, 4] });

    const apres = changerDeColonne(etat, 1, "realisation", 1);

    expect(ids(apres!.cadrage)).toEqual([2]);
    expect(ids(apres!.realisation)).toEqual([3, 1, 4]);
  });

  it("accueille une carte dans une phase vide", () => {
    const apres = changerDeColonne(colonnes({ cadrage: [1] }), 1, "validation", 0);

    expect(ids(apres!.cadrage)).toEqual([]);
    expect(ids(apres!.validation)).toEqual([1]);
  });

  it("ne rend rien quand la carte est déjà dans cette phase", () => {
    expect(changerDeColonne(colonnes({ cadrage: [1, 2] }), 1, "cadrage", 1)).toBeNull();
  });

  it("ne rend rien pour une carte inconnue", () => {
    expect(changerDeColonne(colonnes({ cadrage: [1] }), 99, "cadrage", 0)).toBeNull();
  });

  it("laisse les autres phases intactes", () => {
    const etat = colonnes({ cadrage: [1], realisation: [2], exploitation: [3] });

    const apres = changerDeColonne(etat, 1, "realisation", 0)!;

    expect(apres.exploitation).toBe(etat.exploitation);
  });
});

describe("reordonner", () => {
  it("déplace la carte au rang visé dans sa phase", () => {
    const apres = reordonner(colonnes({ cadrage: [1, 2, 3] }), 1, 2);

    expect(ids(apres!.cadrage)).toEqual([2, 3, 1]);
  });

  it("remonte une carte vers le haut de la phase", () => {
    const apres = reordonner(colonnes({ cadrage: [1, 2, 3] }), 3, 0);

    expect(ids(apres!.cadrage)).toEqual([3, 1, 2]);
  });

  it("ne rend rien quand la carte ne bouge pas", () => {
    expect(reordonner(colonnes({ cadrage: [1, 2, 3] }), 2, 1)).toBeNull();
  });
});
