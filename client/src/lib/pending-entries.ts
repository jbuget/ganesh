import type { MonthGridResponse } from "@/lib/api/generated/model";
import type { DayValue } from "@/lib/day-value";

/**
 * Cells clicked whose write has not left yet.
 *
 * Entering half a day is two clicks on one cell, and the cycle reads the value
 * the cell shows. Read from the server, the second click lands before the first
 * write has come back and reads `0` again: one asks for half a day and gets a
 * whole one. The value the eye is on therefore lives here until the write goes
 * out, and the grid reads it over what the server holds.
 */
export type PendingEntries = Record<string, DayValue>;

/** A cell, named by the month it belongs to as much as by its place in it. */
export interface PendingCell {
  userId: number;
  projectId: number;
  /**
   * The trade the cell is declared under. Null on off-project work.
   *
   * Part of what names the cell: two trades of one mission hold two cells on
   * the same day, and a key that left the trade out would have the second
   * click overwrite the first — the very thing this queue exists to prevent.
   */
  activityId: number | null;
  day: string;
}

/**
 * Under which a cell's pending value is held.
 *
 * The key names whose month the cell is in, and not only where it sits: one
 * walks from one's own month to a colleague's while a write is still waiting,
 * and a value read or written under the wrong name is a day declared for
 * somebody else.
 */
export function pendingKey({
  userId,
  projectId,
  activityId,
  day,
}: PendingCell): string {
  return `${userId}:${projectId}:${activityId ?? ""}:${day}`;
}

/** The cell a key names. */
export function pendingCell(key: string): PendingCell {
  const [userId, projectId, activityId, day] = key.split(":");
  return {
    userId: Number(userId),
    projectId: Number(projectId),
    activityId: activityId === "" ? null : Number(activityId),
    day,
  };
}

/** Days are halves: summing them in floats is what gives 0.30000000000000004. */
function round(value: number): number {
  return Math.round(value * 100) / 100;
}

/**
 * The grid as the eye reads it: what the server holds, cells awaiting a write
 * laid over it.
 *
 * The totals move with the cells rather than waiting for the write to come
 * back. A day's total carries a colour — green when the day is complete, red
 * when it is not — and that is exactly what one is watching while clicking a
 * second time: a total half a second behind would call a day incomplete that
 * has just been completed.
 *
 * What a forecast is, is settled in the domain, and read here the same way: a
 * day past today is delivered, a day ahead of it is forecast.
 */
export function withPendingEntries(
  grid: MonthGridResponse,
  pending: PendingEntries,
  today: string,
): MonthGridResponse {
  const cells = Object.keys(pending)
    .map((key) => ({ ...pendingCell(key), value: pending[key] }))
    // Only this month's, and only this person's: the rest is waiting for the
    // grid it was clicked on.
    .filter((cell) => cell.userId === grid.user_id);
  if (cells.length === 0) return grid;

  const dayDeltas = new Map<string, number>();
  let actualDelta = 0;
  let forecastDelta = 0;

  const rows = grid.rows.map((row) => {
    const here = cells.filter(
      (cell) =>
        cell.projectId === row.project_id &&
        cell.activityId === (row.activity_id ?? null),
    );
    if (here.length === 0) return row;

    const values = { ...row.values };
    let actual = 0;
    let forecast = 0;

    for (const { day, value } of here) {
      const delta = value - (values[day] ?? 0);
      // An empty cell carries no entry, and the server sends none: writing a
      // 0 would make the grid read differently before and after the refresh.
      if (value === 0) delete values[day];
      else values[day] = value;
      if (delta === 0) continue;

      if (day > today) forecast = round(forecast + delta);
      else actual = round(actual + delta);
      dayDeltas.set(day, round((dayDeltas.get(day) ?? 0) + delta));
    }

    actualDelta = round(actualDelta + actual);
    forecastDelta = round(forecastDelta + forecast);

    return {
      ...row,
      values,
      actual_total: round(row.actual_total + actual),
      forecast_total: round(row.forecast_total + forecast),
      total: round(row.total + actual + forecast),
      // What the project has consumed counts delivered time alone, forecast
      // excluded — the same reading as the row's own.
      total_consumed_days: round(row.total_consumed_days + actual),
    };
  });

  const day_totals = grid.day_totals.map((dayTotal) => {
    const delta = dayDeltas.get(dayTotal.day);
    if (delta === undefined || delta === 0) return dayTotal;
    const total = round(dayTotal.total + delta);
    return { ...dayTotal, total, exceeds_capacity: total > 1 };
  });

  return {
    ...grid,
    rows,
    day_totals,
    actual_total: round(grid.actual_total + actualDelta),
    forecast_total: round(grid.forecast_total + forecastDelta),
  };
}
