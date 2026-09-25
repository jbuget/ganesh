"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { DayValue } from "@/lib/day-value";
import {
  pendingCell,
  pendingKey,
  type PendingCell,
  type PendingEntries,
} from "@/lib/pending-entries";

/**
 * How long a cell waits before its value is written.
 *
 * Long enough that the two or three clicks it takes to reach half a day, or to
 * empty a cell, read as the one gesture they are: a single write goes out, with
 * the value landed on. Short enough that the write is gone before one moves on.
 */
const SETTLE = 400;

interface Writes {
  /** Writes one cell. A rejection rolls the cell back, silently. */
  write: (cell: PendingCell, value: DayValue) => Promise<void>;
  /** Replays the month's queries, once the writes are through. */
  refresh: () => Promise<void>;
}

/**
 * Cells clicked, written once they have settled.
 *
 * The clicks are answered on the spot — the grid reads `pending` over what the
 * server holds — and the writes leave together once the hand has stopped. A
 * cell clicked four times is one write rather than four, and the cycle always
 * reads the value the eye is on.
 *
 * A write that fails says nothing: the cell goes back to the value the server
 * holds, which is the one answer that does not report an entry nobody stored.
 */
export function usePendingEntries({ write, refresh }: Writes) {
  const [pending, setPending] = useState<PendingEntries>({});

  // What is pending is read outside a render — by the timer, and by the flush
  // a gesture on the month asks for — so it is held in a ref as well as in
  // state.
  const held = useRef<PendingEntries>({});
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Writes are chained rather than fired as they come: two writes crossing on
  // one cell could land in the order the network chose rather than the one the
  // hand clicked.
  const queue = useRef<Promise<void>>(Promise.resolve());
  // The screen is rebuilt on every click; what writes must be the latest.
  const writes = useRef<Writes>({ write, refresh });
  useEffect(() => {
    writes.current = { write, refresh };
  });

  const hold = useCallback((next: PendingEntries) => {
    held.current = next;
    setPending(next);
  }, []);

  const drain = useCallback(async () => {
    const written = { ...held.current };
    const keys = Object.keys(written);
    if (keys.length === 0) return;

    for (const key of keys) {
      try {
        await writes.current.write(pendingCell(key), written[key]);
      } catch {
        // Nothing is said: the refresh below brings the value the server holds
        // and the cell goes back to it.
      }
    }

    try {
      await writes.current.refresh();
    } catch {
      // The grid stays as it was; the cells are let go all the same.
    }

    // Only what was written is let go: a cell clicked again while the write was
    // in flight is still waiting for its own.
    const left = Object.fromEntries(
      Object.entries(held.current).filter(([key, value]) => written[key] !== value),
    );
    hold(left);
  }, [hold]);

  /** Sends what is waiting now, without waiting for it to settle. */
  const flush = useCallback((): Promise<void> => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
    // A link that broke does not stop the chain.
    queue.current = queue.current.catch(() => {}).then(drain);
    return queue.current;
  }, [drain]);

  /** Takes a cell's new value, and pushes back the moment it is written. */
  const setValue = useCallback(
    (cell: PendingCell, value: DayValue) => {
      hold({ ...held.current, [pendingKey(cell)]: value });
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => void flush(), SETTLE);
    },
    [flush, hold],
  );

  // Leaving the screen writes what is waiting: the grid goes, the entry does
  // not.
  useEffect(() => () => void flush(), [flush]);

  return { pending, setValue, flush };
}
