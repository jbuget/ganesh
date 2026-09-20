/**
 * Reading what the register holds on a teammate.
 *
 * The panel says three things about someone: what they work on, what they
 * declared lately, and where their months stand. The first two are read as
 * they come; the months need working out, and that is what lives here.
 */
import type { MonthFillingResponse } from "@/lib/api/generated/model";
import { formatMonth, formatWeek } from "@/lib/dates";

/** The stretch declared time was read over: « du 19 août au 17 sept. ». */
export function windowLabel(since: string, until: string): string {
  return `du ${formatWeek(since)} au ${formatWeek(until)}`;
}

/** One month of somebody's sheet, as the panel reads it. */
export interface MonthReading {
  /** The first day of the month, as the address names it. */
  month: string;
  label: string;
  delivered: number;
  forecast: number;
  /** Working days the month has already called for. */
  expected: number;
  workingDays: number;
  /** Days already gone with nothing declared against them. */
  missing: number;
  deliveredShare: number;
  forecastShare: number;
  isRunning: boolean;
  isValidated: boolean;
  validatedAt: string | null;
}

function readMonth(filling: MonthFillingResponse, today: string): MonthReading {
  const [year, month] = filling.month.slice(0, 10).split("-").map(Number);

  // Against the whole month, as on the home screen: the bar says how full the
  // month is, and the figures beside it say against what.
  const share = (days: number) =>
    filling.working_days === 0
      ? 0
      : Math.min(100, Math.round((days / filling.working_days) * 100));
  const deliveredShare = share(filling.delivered);

  return {
    month: filling.month,
    label: formatMonth(year, month),
    delivered: filling.delivered,
    forecast: filling.forecast,
    expected: filling.elapsed_working_days,
    workingDays: filling.working_days,
    // Never negative: a day declared twice over is a warning of its own, in
    // the grid, and must not read here as time owed the other way.
    missing: Math.max(0, filling.elapsed_working_days - filling.delivered),
    deliveredShare,
    // Set back from what is delivered, and cut at the bar's own width: what is
    // planned must never read as done, nor push the bar past the month.
    forecastShare: Math.min(share(filling.forecast), 100 - deliveredShare),
    isRunning: filling.month.slice(0, 7) === today.slice(0, 7),
    isValidated: filling.state === "validated",
    validatedAt: filling.validated_at ?? null,
  };
}

/** The months of somebody's sheet, in the order they came back. */
export function readMonths(
  fillings: MonthFillingResponse[],
  today: string,
): MonthReading[] {
  return fillings.map((filling) => readMonth(filling, today));
}
