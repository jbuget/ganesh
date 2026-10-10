/**
 * Reading the dashboard figures out loud.
 *
 * Every figure here can be absent. A window may expect nothing of anyone — a
 * weekend, a period closing no month — and « 0 % » would then read as a
 * failure that is not one. An em dash says « there is nothing to read », which
 * is a different statement.
 */
import type {
  ActivityDayResponse,
  IntakeResponse,
  PeriodRange,
  PeriodResponse,
  SteeringResponse,
  WorkNature,
} from "@/lib/api/generated/model";
import { category, phaseDot, phaseLabel } from "@/lib/board";
import { workNatureLabel } from "@/lib/work-natures";

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
  // Two decimals: a day is declared down to the quarter, and one decimal
  // showed 12.25 as « 12,3 » — a figure nobody declared.
  return decimal(days, 2);
}

export function formatDelay(days: number | null | undefined): string {
  if (days === null || days === undefined) return NOTHING;
  if (days === 0) return "le jour même";
  return `${decimal(days)} j`;
}

/** How long a need has waited for an answer: « 12 j », never a bare number. */
export function formatWait(days: number | null | undefined): string {
  if (days === null || days === undefined) return NOTHING;
  if (days === 0) return "depuis aujourd'hui";
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

/**
 * The first of the month is « 1er », never « 1 ».
 *
 * `Intl` does not do it, and the anchored windows make the case the common
 * one rather than the exception: every month opens on a first.
 */
function ordinal(day: number): string {
  return day === 1 ? "1er" : String(day);
}

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
    return `Le ${fullDate(start)} · ${days}`;
  }

  const sameYear = start.getFullYear() === end.getFullYear();
  const sameMonth = sameYear && start.getMonth() === end.getMonth();
  const from = sameMonth
    ? ordinal(start.getDate())
    : sameYear
      ? dayAndMonth(start)
      : fullDate(start);

  return `Du ${from} au ${fullDate(end)} · ${days}`;
}

function dayAndMonth(date: Date): string {
  return DAY_AND_MONTH.format(date).replace(/^1\b/, "1er");
}

function fullDate(date: Date): string {
  return FULL_DATE.format(date).replace(/^1\b/, "1er");
}

/**
 * Turning the steering block into lines a breakdown can draw.
 *
 * Phases and axes keep the labels and the colours they carry on the board: the
 * same mission must be recognisable from one screen to the next.
 */
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
      label: "Sur projet",
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

/** One slice of a bar split into parts: what it is, how much, what colour. */
export interface BarSegment {
  key: string;
  label: string;
  days: number;
  /** Share of the bar, which is the sum of its own segments. */
  share: number;
  /** A hex colour: the chart palette's, not a Tailwind class. */
  colour: string;
}

/**
 * One colour per trade, fixed.
 *
 * The first three slots of the chart palette, which hold together in every
 * pair. A colour follows the trade and never its rank: a quiet week must not
 * repaint design.
 */
const TRADE_COLOURS: Record<WorkNature, string> = {
  development: "#2a78d6",
  design: "#eb6834",
  project_management: "#1baf7a",
};

/** What states no trade is neutral: it is a gap in the data, not a trade. */
const NO_TRADE_COLOUR = "#94a3b8";

/**
 * Turning the project time per trade into the parts of one bar.
 *
 * Shares are read over the project time alone. Off-project work carries no
 * trade, so a share taken over everything declared would never reach a
 * hundred and the bar would end short of its frame.
 */
export function tradeSegments(steering: SteeringResponse): BarSegment[] {
  if (steering.project_days === 0) return [];

  return steering.by_nature.map((row) => ({
    key: row.nature ?? "none",
    label: workNatureLabel(row.nature) ?? "Sans métier précisé",
    days: row.days,
    share: row.days / steering.project_days,
    colour: row.nature ? TRADE_COLOURS[row.nature] : NO_TRADE_COLOUR,
  }));
}

/** One line of the recueil's movements: what it is, and how many. */
export interface CountRow {
  key: string;
  label: string;
  count: number;
}

/**
 * What the company asked for over the window, and what became of it.
 *
 * Asked, then answered, then built. It is not a funnel: a need accepted today
 * may have been handed over last month, so the lines are never read as shares
 * of the first one.
 */
export function intakeRows(intake: IntakeResponse): CountRow[] {
  const rows: CountRow[] = [
    { key: "submitted", label: "Déposés", count: intake.submitted },
    { key: "accepted", label: "Acceptés", count: intake.accepted },
    { key: "rejected", label: "Refusés", count: intake.rejected },
    { key: "deferred", label: "Reportés", count: intake.deferred },
    { key: "converted", label: "Devenus des projets", count: intake.converted },
  ];
  return rows.every((row) => row.count === 0) ? [] : rows;
}

/** The shades of the mosaic: 0 is a quiet day, 4 the busiest of the window. */
export type ActivityLevel = 0 | 1 | 2 | 3 | 4;

/**
 * The shade of a day, relative to the busiest one of the window.
 *
 * Relative rather than fixed thresholds: a team of fifteen and a team of
 * five do not make the same number of gestures, and a fixed scale would paint
 * either the whole mosaic or none of it. A single gesture is never read as
 * nothing — the day was lived in.
 */
export function activityLevel(gestures: number, busiest: number): ActivityLevel {
  if (gestures <= 0 || busiest <= 0) return 0;
  return Math.max(1, Math.ceil((gestures / busiest) * 4)) as ActivityLevel;
}

/** One column: Monday to Sunday, a slot left empty where the window is not. */
export type ActivityWeek = (ActivityDayResponse | undefined)[];

/**
 * The window as a calendar: one column per week, Monday at the top.
 *
 * The first and the last column are padded with empty slots, so that a day
 * always sits on the row of its weekday whichever day the window opens on.
 */
export function activityWeeks(days: ActivityDayResponse[]): ActivityWeek[] {
  const weeks: ActivityWeek[] = [];

  for (const entry of days) {
    // Monday is 0: `getDay` opens its week on Sunday.
    const weekday = (parse(entry.day).getDay() + 6) % 7;
    if (weeks.length === 0 || weekday === 0) {
      weeks.push(Array.from({ length: 7 }, () => undefined));
    }
    weeks[weeks.length - 1][weekday] = entry;
  }
  return weeks;
}

const WEEKDAY_AND_DATE = new Intl.DateTimeFormat("fr-FR", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

/** « vendredi 9 octobre », the first of the month as « 1er ». */
export function formatWeekdayAndDate(iso: string): string {
  return WEEKDAY_AND_DATE.format(parse(iso)).replace(/ 1 /, " 1er ");
}

/** « 1 geste », « 4 gestes »: the count and its noun, which agrees with it. */
export function formatGestures(gestures: number): string {
  return `${gestures.toLocaleString("fr-FR")} geste${gestures > 1 ? "s" : ""}`;
}

/** What a cell says to whoever cannot see its shade: « 4 gestes le vendredi 9 octobre ». */
export function describeActivityDay(entry: ActivityDayResponse): string {
  const when = formatWeekdayAndDate(entry.day);
  if (entry.gestures === 0) return `Aucun geste le ${when}`;
  return `${formatGestures(entry.gestures)} le ${when}`;
}

const MONTH_SHORT = new Intl.DateTimeFormat("fr-FR", { month: "short" });

/** Columns the label of a month needs before the next one may follow it. */
const MONTH_LABEL_WIDTH = 3;

/**
 * The month written above the column it opens in, and nothing above the rest.
 *
 * A column is read by its first day. A label squeezed against the next one
 * would overlap it, so the earlier of two close labels gives way: the window
 * opens mid-month, and its first month is the one that ends up crowded.
 */
export function activityMonthLabels(weeks: ActivityWeek[]): string[] {
  const opened: { column: number; month: number }[] = [];

  weeks.forEach((week, column) => {
    const first = week.find((entry) => entry !== undefined);
    if (!first) return;
    const month = parse(first.day).getMonth();
    if (opened.length === 0 || opened[opened.length - 1].month !== month) {
      opened.push({ column, month });
    }
  });

  const labels = weeks.map(() => "");
  opened.forEach((entry, index) => {
    const next = opened[index + 1];
    if (next && next.column - entry.column < MONTH_LABEL_WIDTH) return;
    const first = weeks[entry.column].find((slot) => slot !== undefined);
    if (first) labels[entry.column] = MONTH_SHORT.format(parse(first.day));
  });
  return labels;
}

/** What a day weighs in the year's gestures: « 14,3 % », one decimal. */
export function formatYearShare(gestures: number, total: number): string {
  if (total === 0) return NOTHING;
  return `${(Math.round((gestures / total) * 1000) / 10).toLocaleString("fr-FR")} %`;
}
