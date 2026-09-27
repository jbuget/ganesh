"use client";

import { useDigest } from "@/lib/api/queries";
import { firstDayOfMonth, todayIso, type MonthCursor } from "@/lib/dates";

/**
 * The month La Gazette is at, for the band on the home screen.
 *
 * A query of its own rather than one more field of `useHome`: the home screen
 * waits on four month grids before it draws anything on the left, and holding
 * a band that reads one digest behind them would leave the right-hand column
 * half-empty for as long as the slowest of them travels. The mood is read the
 * same way, and for the same reason.
 *
 * The running month, always — never a cursor the reader moves. Moving through
 * the months is what the screen is for, and a band that could be walked back
 * would be that screen, badly.
 */
export function useGazetteBand() {
  const today = todayIso();
  const cursor: MonthCursor = {
    year: Number(today.slice(0, 4)),
    month: Number(today.slice(5, 7)),
  };

  const { digest, isLoading } = useDigest(
    firstDayOfMonth(cursor.year, cursor.month),
    null,
  );

  return { cursor, digest, isLoading };
}
