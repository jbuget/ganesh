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
  it("returns the phase and rank of a card", () => {
    const state = columns({ scoping: [1, 2], development: [3] });

    expect(locate(state, 2)).toEqual({ status: "scoping", position: 1 });
    expect(locate(state, 3)).toEqual({ status: "development", position: 0 });
  });

  it("returns null for a card absent from the board", () => {
    expect(locate(columns({ scoping: [1] }), 99)).toBeNull();
  });
});

describe("indexVise", () => {
  it("inserts before the hovered card", () => {
    expect(targetIndex(columns({ scoping: [1, 2, 3] }).scoping, 2, false)).toBe(1);
  });

  it("inserts after the hovered card once past it", () => {
    expect(targetIndex(columns({ scoping: [1, 2, 3] }).scoping, 2, true)).toBe(2);
  });

  it("aims at the end when no card is hovered", () => {
    expect(targetIndex(columns({ scoping: [1, 2, 3] }).scoping, null, false)).toBe(3);
  });
});

describe("changerDeColonne", () => {
  it("removes the card from its phase and inserts it into the new one", () => {
    const state = columns({ scoping: [1, 2], development: [3, 4] });

    const apres = moveToColumn(state, 1, "development", 1);

    expect(ids(apres!.scoping)).toEqual([2]);
    expect(ids(apres!.development)).toEqual([3, 1, 4]);
  });

  it("takes a card into an empty phase", () => {
    const apres = moveToColumn(columns({ scoping: [1] }), 1, "validation", 0);

    expect(ids(apres!.scoping)).toEqual([]);
    expect(ids(apres!.validation)).toEqual([1]);
  });

  it("returns nothing when the card is already in that phase", () => {
    expect(moveToColumn(columns({ scoping: [1, 2] }), 1, "scoping", 1)).toBeNull();
  });

  it("returns nothing for an unknown card", () => {
    expect(moveToColumn(columns({ scoping: [1] }), 99, "scoping", 0)).toBeNull();
  });

  it("leaves the other phases untouched", () => {
    const state = columns({ scoping: [1], development: [2], operations: [3] });

    const apres = moveToColumn(state, 1, "development", 0)!;

    expect(apres.operations).toBe(state.operations);
  });
});

describe("reordonner", () => {
  it("moves the card to the rank aimed at within its phase", () => {
    const apres = reorder(columns({ scoping: [1, 2, 3] }), 1, 2);

    expect(ids(apres!.scoping)).toEqual([2, 3, 1]);
  });

  it("lifts a card towards the top of the phase", () => {
    const apres = reorder(columns({ scoping: [1, 2, 3] }), 3, 0);

    expect(ids(apres!.scoping)).toEqual([3, 1, 2]);
  });

  it("returns nothing when the card does not move", () => {
    expect(reorder(columns({ scoping: [1, 2, 3] }), 2, 1)).toBeNull();
  });
});
