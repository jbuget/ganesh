import { describe, expect, it } from "vitest";

import { moveToColumn, targetIndex, locate, reorder } from "./board-move";
import type { BoardCardResponse, ProjectStatus } from "@/lib/api/generated/model";
import type { Columns } from "@/lib/use-board";
import { PHASES } from "@/lib/board";

const card = (id: number): BoardCardResponse =>
  ({
    project: { id, label: `Mission ${id}` },
    consumed_days: 0,
    contributors: [],
  }) as unknown as BoardCardResponse;

/** Empty columns, filled in by those a test describes. */
const columns = (filled: Partial<Record<ProjectStatus, number[]>>): Columns =>
  Object.fromEntries(
    PHASES.map(({ status }) => [status, (filled[status] ?? []).map(card)]),
  ) as Columns;

const ids = (cards: BoardCardResponse[]) => cards.map((c) => c.project.id);

describe("locate", () => {
  it("returns the phase and rank of a card", () => {
    const state = columns({ scoping: [1, 2], development: [3] });

    expect(locate(state, 2)).toEqual({ status: "scoping", position: 1 });
    expect(locate(state, 3)).toEqual({ status: "development", position: 0 });
  });

  it("returns null for a card absent from the board", () => {
    expect(locate(columns({ scoping: [1] }), 99)).toBeNull();
  });
});

describe("targetIndex", () => {
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

describe("moveToColumn", () => {
  it("removes the card from its phase and inserts it into the new one", () => {
    const state = columns({ scoping: [1, 2], development: [3, 4] });

    const after = moveToColumn(state, 1, "development", 1);

    expect(ids(after!.scoping)).toEqual([2]);
    expect(ids(after!.development)).toEqual([3, 1, 4]);
  });

  it("takes a card into an empty phase", () => {
    const after = moveToColumn(columns({ scoping: [1] }), 1, "validation", 0);

    expect(ids(after!.scoping)).toEqual([]);
    expect(ids(after!.validation)).toEqual([1]);
  });

  it("returns nothing when the card is already in that phase", () => {
    expect(moveToColumn(columns({ scoping: [1, 2] }), 1, "scoping", 1)).toBeNull();
  });

  it("returns nothing for an unknown card", () => {
    expect(moveToColumn(columns({ scoping: [1] }), 99, "scoping", 0)).toBeNull();
  });

  it("leaves the other phases untouched", () => {
    const state = columns({ scoping: [1], development: [2], operations: [3] });

    const after = moveToColumn(state, 1, "development", 0)!;

    expect(after.operations).toBe(state.operations);
  });
});

describe("reorder", () => {
  it("moves the card to the rank aimed at within its phase", () => {
    const after = reorder(columns({ scoping: [1, 2, 3] }), 1, 2);

    expect(ids(after!.scoping)).toEqual([2, 3, 1]);
  });

  it("lifts a card towards the top of the phase", () => {
    const after = reorder(columns({ scoping: [1, 2, 3] }), 3, 0);

    expect(ids(after!.scoping)).toEqual([3, 1, 2]);
  });

  it("returns nothing when the card does not move", () => {
    expect(reorder(columns({ scoping: [1, 2, 3] }), 2, 1)).toBeNull();
  });
});

/**
 * A filtered board shows some cards of each phase and hides the others, but
 * the moves are computed on the whole phase: the rank saved is the one the
 * server knows, and the hidden cards keep their place around the one moved.
 */
describe("on a filtered board", () => {
  // Phase « development » holds 3, 4 (hidden), 5, 6 (hidden); only 3 and 5
  // show.
  const state = () => columns({ scoping: [1, 2], development: [3, 4, 5, 6] });

  it("drops a card right before the shown card it was aimed at", () => {
    const index = targetIndex(state().development, 5, false);

    const after = moveToColumn(state(), 1, "development", index)!;

    expect(ids(after.development)).toEqual([3, 4, 1, 5, 6]);
  });

  it("drops a card right after the shown card it went past", () => {
    const index = targetIndex(state().development, 3, true);

    const after = moveToColumn(state(), 1, "development", index)!;

    expect(ids(after.development)).toEqual([3, 1, 4, 5, 6]);
  });

  it("sends a card dropped below every shown one to the end of the phase", () => {
    const index = targetIndex(state().development, null, false);

    const after = moveToColumn(state(), 1, "development", index)!;

    expect(ids(after.development)).toEqual([3, 4, 5, 6, 1]);
  });

  it("lowers a card next to the shown card it was dropped on", () => {
    const hovered = locate(state(), 5)!;

    const after = reorder(state(), 3, hovered.position)!;

    expect(ids(after.development)).toEqual([4, 5, 3, 6]);
  });

  it("raises a card next to the shown card it was dropped on", () => {
    const hovered = locate(state(), 3)!;

    const after = reorder(state(), 5, hovered.position)!;

    expect(ids(after.development)).toEqual([5, 3, 4, 6]);
  });
});
