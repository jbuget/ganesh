import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import type { DayValue } from "@/lib/day-value";
import { pendingKey, type PendingCell } from "@/lib/pending-entries";
import { usePendingEntries } from "./use-pending-entries";

const SETTLE = 400;
const cell: PendingCell = {
  userId: 1,
  projectId: 10,
  activityId: null,
  day: "2026-09-14",
};

let write: Mock<(cell: PendingCell, value: DayValue) => Promise<void>>;
let refresh: Mock<() => Promise<void>>;

function entries() {
  const { result, unmount } = renderHook(() => usePendingEntries({ write, refresh }));
  return { result, unmount };
}

/** Lets the timer go off, and the writes it starts run to the end. */
async function settle(by: number = SETTLE) {
  await act(async () => {
    vi.advanceTimersByTime(by);
  });
}

function click(
  result: { current: ReturnType<typeof usePendingEntries> },
  value: DayValue,
) {
  act(() => result.current.setValue(cell, value));
}

beforeEach(() => {
  vi.useFakeTimers();
  write = vi.fn().mockResolvedValue(undefined);
  refresh = vi.fn().mockResolvedValue(undefined);
});

afterEach(() => {
  vi.useRealTimers();
});

describe("cells clicked, written once they have settled", () => {
  /**
   * The gesture that entered a whole day where half a day was meant: two
   * clicks, two writes, and the second reading a cell the first had not come
   * back to yet.
   */
  it("writes one cell once, whatever the number of clicks it took", async () => {
    const { result } = entries();

    click(result, 1);
    click(result, 0.5);
    await settle();

    expect(write).toHaveBeenCalledTimes(1);
    expect(write).toHaveBeenCalledWith(cell, 0.5);
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("shows the value clicked before anything is written", () => {
    const { result } = entries();

    click(result, 1);

    expect(result.current.pending).toEqual({ [pendingKey(cell)]: 1 });
    expect(write).not.toHaveBeenCalled();
  });

  it("holds the write back as long as the clicking goes on", async () => {
    const { result } = entries();

    click(result, 1);
    await settle(SETTLE - 100);
    click(result, 0.5);
    await settle(SETTLE - 100);

    expect(write).not.toHaveBeenCalled();
  });

  it("lets the cell go once the grid has been read again", async () => {
    const { result } = entries();

    click(result, 1);
    await settle();

    expect(result.current.pending).toEqual({});
  });

  /**
   * The cell goes back to the value the server holds: saying nothing is the
   * one answer that does not report an entry nobody stored.
   */
  it("lets a cell go silently when its write is refused", async () => {
    write.mockRejectedValue(new Error("month validated"));
    const { result } = entries();

    click(result, 1);
    await settle();

    expect(result.current.pending).toEqual({});
    expect(refresh).toHaveBeenCalled();
  });

  it("sends what is waiting on demand, without waiting for it to settle", async () => {
    const { result } = entries();

    click(result, 1);
    await act(async () => {
      await result.current.flush();
    });

    expect(write).toHaveBeenCalledWith(cell, 1);
  });

  it("has nothing to send when no cell is waiting", async () => {
    const { result } = entries();

    await act(async () => {
      await result.current.flush();
    });

    expect(write).not.toHaveBeenCalled();
    expect(refresh).not.toHaveBeenCalled();
  });

  /** The grid goes, the entry does not. */
  it("writes what is waiting when the screen is left", async () => {
    const { result, unmount } = entries();
    click(result, 1);

    unmount();
    await act(async () => {});

    expect(write).toHaveBeenCalledWith(cell, 1);
  });

  /**
   * Writes are chained rather than fired as they come: two writes on one cell
   * crossing could land in the order the network chose.
   */
  it("keeps a cell clicked again while its write was in flight", async () => {
    let answer: () => void = () => {};
    write.mockImplementationOnce(
      () =>
        new Promise<void>((resolve) => {
          answer = resolve;
        }),
    );
    const { result } = entries();

    click(result, 1);
    await settle();
    click(result, 0.5);
    act(() => answer());
    await settle();

    expect(write.mock.calls).toEqual([
      [cell, 1],
      [cell, 0.5],
    ]);
  });
});
