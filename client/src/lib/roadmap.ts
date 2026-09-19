/**
 * Reading a roadmap: where a bar sits on the axis, and how the lines group.
 *
 * All of it is pure and lives here rather than in the components: placing a
 * segment is arithmetic, and arithmetic is worth testing. The components are
 * left with the drawing.
 */
import {
  CATEGORIES,
  PHASES,
  PRIORITIES,
  category as axisOf,
  phaseLabel,
  priority as urgencyOf,
} from "@/lib/board";
import type {
  RoadmapMissionResponse,
  RoadmapSummaryResponse,
  SegmentKind,
} from "@/lib/api/generated/model";

const MS_PER_DAY = 86_400_000;

/** An ISO day as a UTC timestamp — no time zone, no drift. */
function utc(isoDay: string): number {
  const [year, month, day] = isoDay.split("-").map(Number);
  return Date.UTC(year, month - 1, day);
}

/** Whole days from one ISO day to another. Negative when it runs backwards. */
export function daysBetween(from: string, to: string): number {
  return Math.round((utc(to) - utc(from)) / MS_PER_DAY);
}

/** The ISO day `count` days after `from`. */
export function dayAfter(from: string, count: number): string {
  return new Date(utc(from) + count * MS_PER_DAY).toISOString().slice(0, 10);
}

/**
 * Where a day falls in the window, as a share of its width.
 *
 * Unclamped on purpose: a caller placing a bar needs to know it starts before
 * the window, not to be told it starts on the first day.
 */
export function positionOf(day: string, from: string, to: string): number {
  const width = daysBetween(from, to) + 1;
  return width <= 0 ? 0 : daysBetween(from, day) / width;
}

/** Where a stretch of days sits in the window, clipped to it. */
export interface Placement {
  /** Share of the width the stretch starts at, from 0 to 1. */
  left: number;
  /** Share of the width it covers. Never zero: a one-day bar must show. */
  width: number;
  /** Whether it reaches out of the window, and which way. */
  clippedLeft: boolean;
  clippedRight: boolean;
}

/**
 * Places a stretch of days on the axis, or nothing when it misses the window.
 *
 * A stretch reaching out of the window is cut and says so: drawing it flush
 * with the edge would read as « it starts here », which is a different claim.
 */
export function placeOn(
  startsOn: string,
  endsOn: string,
  from: string,
  to: string,
): Placement | null {
  if (endsOn < from || startsOn > to) return null;

  const clippedLeft = startsOn < from;
  const clippedRight = endsOn > to;
  const left = Math.max(0, positionOf(startsOn, from, to));
  // The end of a day is the start of the next: a bar covering a single day
  // must be a day wide, not nothing wide.
  const right = Math.min(1, positionOf(dayAfter(endsOn, 1), from, to));

  return { left, width: Math.max(right - left, 0.002), clippedLeft, clippedRight };
}

const MONTH_ABBREVIATIONS = [
  "janv.",
  "févr.",
  "mars",
  "avr.",
  "mai",
  "juin",
  "juil.",
  "août",
  "sept.",
  "oct.",
  "nov.",
  "déc.",
];

export interface MonthTick {
  /** `YYYY-MM`, which is what React keys on. */
  key: string;
  label: string;
  /** Whether the month opens a year, which is when the year is spelled out. */
  opensYear: boolean;
  /** Share of the window's width this month covers. */
  width: number;
}

/**
 * The months a window spans, with the width each one takes.
 *
 * Widths rather than equal columns: February is shorter than March, and a
 * scale that pretended otherwise would put every bar a day or two off.
 */
export function monthsOf(from: string, to: string): MonthTick[] {
  const total = daysBetween(from, to) + 1;
  if (total <= 0) return [];

  const ticks: MonthTick[] = [];
  let [year, month] = from.split("-").map(Number);

  while (true) {
    const firstOfMonth = `${year}-${String(month).padStart(2, "0")}-01`;
    const nextYear = month === 12 ? year + 1 : year;
    const nextMonth = month === 12 ? 1 : month + 1;
    const firstOfNext = `${nextYear}-${String(nextMonth).padStart(2, "0")}-01`;

    const opens = firstOfMonth < from ? from : firstOfMonth;
    const closes = firstOfNext > to ? dayAfter(to, 1) : firstOfNext;

    ticks.push({
      key: `${year}-${String(month).padStart(2, "0")}`,
      label: MONTH_ABBREVIATIONS[month - 1],
      opensYear: month === 1 || ticks.length === 0,
      width: daysBetween(opens, closes) / total,
    });

    if (firstOfNext > to) break;
    year = nextYear;
    month = nextMonth;
  }

  return ticks;
}

/** How the lines are gathered into bands. */
export type Grouping = "category" | "status" | "priority" | "none";

export const GROUPINGS: { value: Grouping; label: string }[] = [
  { value: "category", label: "Par axe stratégique" },
  { value: "status", label: "Par phase" },
  { value: "priority", label: "Par priorité" },
  { value: "none", label: "Sans regroupement" },
];

export interface Band {
  key: string;
  label: string;
  /** Tailwind class of the band's mark, when it carries one. */
  mark: string | null;
  missions: RoadmapMissionResponse[];
}

/** The label a band with nothing to name it reads under. */
const UNNAMED: Record<Grouping, string> = {
  category: "Sans axe",
  status: "Sans phase",
  priority: "Sans priorité",
  none: "Toutes les missions",
};

/**
 * Gathers the lines into bands, in the order the rest of the application
 * already reads them in.
 *
 * Empty bands are dropped, and what carries nothing to group by comes last:
 * not having declared an axis must not open the reading.
 */
export function bandsOf(
  missions: RoadmapMissionResponse[],
  grouping: Grouping,
): Band[] {
  if (grouping === "none") {
    return missions.length
      ? [{ key: "all", label: UNNAMED.none, mark: null, missions }]
      : [];
  }

  const order = keysInOrder(grouping);
  const bands = new Map<string, RoadmapMissionResponse[]>();
  for (const mission of missions) {
    const key = keyOf(mission, grouping) ?? "";
    bands.set(key, [...(bands.get(key) ?? []), mission]);
  }

  return [...order, ""]
    .filter((key) => bands.has(key))
    .map((key) => ({
      key: key || "none",
      label: key ? labelOf(key, grouping) : UNNAMED[grouping],
      mark: key ? markOf(key, grouping) : null,
      missions: bands.get(key) ?? [],
    }));
}

function keyOf(mission: RoadmapMissionResponse, grouping: Grouping): string | null {
  if (grouping === "category") return mission.category;
  if (grouping === "status") return mission.status;
  return mission.priority;
}

function keysInOrder(grouping: Grouping): string[] {
  if (grouping === "category") return CATEGORIES.map((one) => one.value);
  if (grouping === "status") return PHASES.map((one) => one.status);
  return PRIORITIES.map((one) => one.value);
}

function labelOf(key: string, grouping: Grouping): string {
  if (grouping === "category") return axisOf(key as never)?.label ?? key;
  if (grouping === "status") return phaseLabel(key as never);
  return urgencyOf(key as never)?.label ?? key;
}

function markOf(key: string, grouping: Grouping): string | null {
  if (grouping === "category") return axisOf(key as never)?.bullet ?? null;
  if (grouping === "status") return PHASES.find((p) => p.status === key)?.dot ?? null;
  return null;
}

/**
 * What the drawing is worth, said in one line.
 *
 * Composed here so a test can read it back: a French sentence built at run
 * time is invisible to the type checker, and a rename crossing it would only
 * show when somebody opened the page.
 */
export function roadmapNotice(summary: RoadmapSummaryResponse): string {
  const parts = [`${summary.missions} ${plural(summary.missions, "mission")}`];
  if (summary.delivered > 0)
    parts.push(`${summary.delivered} livrée${s(summary.delivered)}`);
  if (summary.late > 0) parts.push(`${summary.late} en retard`);
  if (summary.undated > 0) parts.push(`${summary.undated} sans date`);
  if (summary.unestimated > 0) parts.push(`${summary.unestimated} sans estimation`);
  return parts.join(" · ");
}

function plural(count: number, word: string): string {
  return count > 1 ? `${word}s` : word;
}

function s(count: number): string {
  return count > 1 ? "s" : "";
}

/** How a segment is drawn, and what that drawing claims. */
export const SEGMENT_STYLES: Record<SegmentKind, { className: string; title: string }> =
  {
    // Solid: it happened.
    lived: { className: "opacity-100", title: "Vécu" },
    // Hatched: the projection supposes it, and nothing more. The stripes are
    // the whole point of this screen — a supposition must never be able to
    // read as a commitment.
    projected: {
      className:
        "opacity-100 [background-image:repeating-linear-gradient(135deg,transparent_0_3px,rgba(255,255,255,0.65)_3px_6px)]",
      title: "Projeté",
    },
    // A thin rule: a service that runs does not end, and must not look like a
    // stretch of work with a length.
    running: { className: "opacity-100", title: "En exploitation" },
  };

/** The civil year, as the two ISO days a window is asked for with. */
export function civilYearOf(year: number): [string, string] {
  return [`${year}-01-01`, `${year}-12-31`];
}
