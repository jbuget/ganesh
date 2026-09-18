import { describe, expect, it } from "vitest";

import { moveToColumn, targetIndex, locate, reorder } from "./board-move";
import type { BoardCardResponse, ProjectStatus } from "@/lib/api/generated/model";
import type { Colonnes } from "@/lib/use-board";
import { PHASES } from "@/lib/board";

const card = (id: number): BoardCardResponse =>
  ({
    project: { id, label: `Mission ${id}` },
    consumed_days: 0,
    contributors: [],
  }) as unknown as BoardCardResponse;

/** Colonnes vides, completees par celles qu'un test decrit. */
const columns = (garnies: Partial<Record<ProjectStatus, number[]>>): Colonnes =>
  Object.fromEntries(
    PHASES.map(({ status }) => [status, (garnies[status] ?? []).map(card)]),
  ) as Colonnes;

const ids = (cards: BoardCardResponse[]) => cards.map((c) => c.project.id);

describe("localiser", () => {
  it("rend la phase et le rang d'une carte", () => {
    const state = columns({ scoping: [1, 2], development: [3] });

    expect(locate(state, 2)).toEqual({ status: "scoping", position: 1 });
    expect(locate(state, 3)).toEqual({ status: "development", position: 0 });
  });

  it("rend null pour une carte absente du tableau", () => {
    expect(locate(columns({ scoping: [1] }), 99)).toBeNull();
  });
});

describe("indexVise", () => {
  it("insère avant la carte survolée", () => {
    expect(targetIndex(columns({ scoping: [1, 2, 3] }).scoping, 2, false)).toBe(1);
  });

  it("insère après la carte survolée quand on la dépasse", () => {
    expect(targetIndex(columns({ scoping: [1, 2, 3] }).scoping, 2, true)).toBe(2);
  });

  it("vise la fin quand aucune carte n'est survolée", () => {
    expect(targetIndex(columns({ scoping: [1, 2, 3] }).scoping, null, false)).toBe(3);
  });
});

describe("changerDeColonne", () => {
  it("retire la carte de sa phase et l'insère dans la nouvelle", () => {
    const state = columns({ scoping: [1, 2], development: [3, 4] });

    const apres = moveToColumn(state, 1, "development", 1);

    expect(ids(apres!.scoping)).toEqual([2]);
    expect(ids(apres!.development)).toEqual([3, 1, 4]);
  });

  it("accueille une carte dans une phase vide", () => {
    const apres = moveToColumn(columns({ scoping: [1] }), 1, "validation", 0);

    expect(ids(apres!.scoping)).toEqual([]);
    expect(ids(apres!.validation)).toEqual([1]);
  });

  it("ne rend rien quand la carte est déjà dans cette phase", () => {
    expect(moveToColumn(columns({ scoping: [1, 2] }), 1, "scoping", 1)).toBeNull();
  });

  it("ne rend rien pour une carte inconnue", () => {
    expect(moveToColumn(columns({ scoping: [1] }), 99, "scoping", 0)).toBeNull();
  });

  it("laisse les autres phases intactes", () => {
    const state = columns({ scoping: [1], development: [2], operations: [3] });

    const apres = moveToColumn(state, 1, "development", 0)!;

    expect(apres.operations).toBe(state.operations);
  });
});

describe("reordonner", () => {
  it("déplace la carte au rang visé dans sa phase", () => {
    const apres = reorder(columns({ scoping: [1, 2, 3] }), 1, 2);

    expect(ids(apres!.scoping)).toEqual([2, 3, 1]);
  });

  it("remonte une carte vers le haut de la phase", () => {
    const apres = reorder(columns({ scoping: [1, 2, 3] }), 3, 0);

    expect(ids(apres!.scoping)).toEqual([3, 1, 2]);
  });

  it("ne rend rien quand la carte ne bouge pas", () => {
    expect(reorder(columns({ scoping: [1, 2, 3] }), 2, 1)).toBeNull();
  });
});
