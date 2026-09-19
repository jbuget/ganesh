/**
 * Reading the dashboard figures out loud.
 *
 * Every figure here can be absent. A window may expect nothing of anyone — a
 * weekend, a period closing no month — and « 0 % » would then read as a
 * failure that is not one. An em dash says « there is nothing to read », which
 * is a different statement.
 */
import type { PeriodRange, PeriodResponse } from "@/lib/api/generated/model";

/** The windows the screen offers, in the order they are shown. */
export const RANGES: { value: PeriodRange; label: string }[] = [
  { value: "today", label: "Aujourd'hui" },
  { value: "yesterday", label: "Hier" },
  { value: "last_7_days", label: "7 derniers jours" },
  { value: "last_30_days", label: "30 derniers jours" },
  { value: "last_90_days", label: "90 derniers jours" },
];

const RANGE_LABELS = new Map(RANGES.map((range) => [range.value, range.label]));

export function rangeLabel(range: PeriodRange): string {
  return RANGE_LABELS.get(range) ?? range;
}

/** Nothing to read: an em dash, never a zero. */
export const NOTHING = "—";

/** A number the French way: a comma, and no trailing zero. */
function decimal(value: number, digits = 1): string {
  return value.toLocaleString("fr-FR", { maximumFractionDigits: digits });
}

export function formatShare(share: number | null | undefined): string {
  if (share === null || share === undefined) return NOTHING;
  return `${Math.round(share * 100)} %`;
}

export function formatPoints(points: number | null | undefined): string {
  if (points === null || points === undefined) return NOTHING;
  // A true minus sign, not a hyphen: at this size the hyphen reads as a dash.
  const sign = points < 0 ? "−" : "+";
  const size = Math.abs(points);
  return `${sign}${decimal(size)} pt${size >= 2 ? "s" : ""}`;
}

export function formatPersonDays(days: number): string {
  return decimal(days);
}

export function formatDelay(days: number | null | undefined): string {
  if (days === null || days === undefined) return NOTHING;
  if (days === 0) return "le jour même";
  return `${decimal(days)} j`;
}

const DAY_AND_MONTH = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "long",
});
const FULL_DATE = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "long",
  year: "numeric",
});

/** Parsed as a local date: `new Date(iso)` would shift the day by a timezone. */
function parse(iso: string): Date {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(year, month - 1, day);
}

/**
 * The window, said as a span: the dates it covers and what it expects.
 *
 * The year is only repeated when the window straddles two, and the month only
 * when it straddles two: a subtitle read at every visit says what changes, not
 * what stays.
 */
export function summarise(period: PeriodResponse): string {
  const start = parse(period.start);
  const end = parse(period.end);

  const days =
    period.working_days === 0
      ? "aucun jour ouvré"
      : `${period.working_days} jour${period.working_days > 1 ? "s" : ""} ouvré${
          period.working_days > 1 ? "s" : ""
        }`;

  if (period.start === period.end) {
    return `Le ${FULL_DATE.format(start)} · ${days}`;
  }

  const sameYear = start.getFullYear() === end.getFullYear();
  const sameMonth = sameYear && start.getMonth() === end.getMonth();
  const from = sameMonth
    ? String(start.getDate())
    : sameYear
      ? DAY_AND_MONTH.format(start)
      : FULL_DATE.format(start);

  return `Du ${from} au ${FULL_DATE.format(end)} · ${days}`;
}

/**
 * Turning the steering block into lines a breakdown can draw.
 *
 * Phases and axes keep the labels and the colours they carry on the board: the
 * same mission must be recognisable from one screen to the next.
 */
import type { SteeringResponse } from "@/lib/api/generated/model";
import { category, phaseDot, phaseLabel } from "@/lib/board";

/** One line of a breakdown: what it is, how many days, what share. */
export interface BreakdownRow {
  key: string;
  label: string;
  days: number;
  share: number | null | undefined;
  colour?: string;
}

export function phaseRows(steering: SteeringResponse): BreakdownRow[] {
  return steering.by_status.map((row) => ({
    key: row.status,
    label: phaseLabel(row.status),
    days: row.days,
    share: row.share,
    colour: phaseDot(row.status),
  }));
}

export function categoryRows(steering: SteeringResponse): BreakdownRow[] {
  return steering.by_category.map((row) => {
    const axis = category(row.category);
    return {
      key: row.category ?? "none",
      label: axis?.label ?? "Sans axe",
      days: row.days,
      share: row.share,
      colour: axis?.bullet ?? "bg-slate-300",
    };
  });
}

export function missionRows(steering: SteeringResponse): BreakdownRow[] {
  return steering.top_missions.map((mission) => ({
    key: String(mission.project_id),
    label: mission.label,
    days: mission.days,
    share: mission.share,
  }));
}

/**
 * Time spent on a mission, against everything that happens around one.
 *
 * Each share is worked out from its own days rather than by subtracting the
 * other: `1 - 0.9` does not give `0.1` in floating point, and the screen would
 * read « 10,000000000000002 % ».
 */
export function kindRows(steering: SteeringResponse): BreakdownRow[] {
  const total = steering.project_days + steering.off_project_days;
  const shareOf = (days: number) => (total === 0 ? null : days / total);

  return [
    {
      key: "project",
      label: "Sur mission",
      days: steering.project_days,
      share: shareOf(steering.project_days),
    },
    {
      key: "off_project",
      label: "Hors projet",
      days: steering.off_project_days,
      share: shareOf(steering.off_project_days),
      colour: "bg-slate-300",
    },
  ];
}
