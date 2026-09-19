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

/** The red thread from the date announced to where the mission lands. */
export interface Slip {
  /** Share of the width the thread starts at, from 0 to 1. */
  left: number;
  /** Share of the width it covers. */
  width: number;
  /**
   * Whether the far end is a day the register holds or one the projection
   * supposes. A fact and a supposition are never drawn alike, and this is
   * what tells the drawing which it has.
   */
  settled: boolean;
}

/**
 * The thread joining the diamond to where the mission lands, clipped to the
 * window.
 *
 * Both ends are cut by the edges and the width is measured **after** the
 * cut: clamping the start alone would keep the whole length and run the
 * thread past the landing, drawing a delay longer than the one computed.
 *
 * A recorded go-live answers before a projection. The two should never meet
 * — a service already live is dropped from the backlog — but a fact outranks
 * a supposition wherever they do.
 */
export function slipOf(
  mission: RoadmapMissionResponse,
  from: string,
  to: string,
): Slip | null {
  const lands = mission.went_live_on ?? mission.landing_date;
  if (!mission.is_late || !mission.target_date || !lands) return null;

  const left = Math.max(0, Math.min(1, positionOf(mission.target_date, from, to)));
  const right = Math.max(0, Math.min(1, positionOf(lands, from, to)));
  if (right <= left) return null;

  return { left, width: right - left, settled: mission.went_live_on !== null };
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

/** The grouping in force, named. */
export function groupingLabel(value: Grouping): string {
  return GROUPINGS.find((one) => one.value === value)?.label ?? value;
}

export interface Band {
  key: string;
  label: string;
  /** Tailwind class of the band's mark, when it carries one. */
  mark: string | null;
  missions: RoadmapMissionResponse[];
  /** Those with a bar or a date: what the band is opened to read. */
  speaking: RoadmapMissionResponse[];
  /**
   * Those with neither. Kept, counted and folded away: they are a fact about
   * the portfolio, and forty of them unfolded drown the dozen that are not.
   */
  silent: RoadmapMissionResponse[];
}

/**
 * Whether a line has anything to draw at all.
 *
 * A date on its own is enough: the diamond sits on the axis and can be read
 * against the others, which a row of two grey words cannot.
 */
export function speaks(mission: RoadmapMissionResponse): boolean {
  return mission.segments.length > 0 || mission.target_date !== null;
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
    return missions.length ? [band("all", UNNAMED.none, null, missions)] : [];
  }

  const order = keysInOrder(grouping);
  const bands = new Map<string, RoadmapMissionResponse[]>();
  for (const mission of missions) {
    const key = keyOf(mission, grouping) ?? "";
    bands.set(key, [...(bands.get(key) ?? []), mission]);
  }

  return [...order, ""]
    .filter((key) => bands.has(key))
    .map((key) =>
      band(
        key || "none",
        key ? labelOf(key, grouping) : UNNAMED[grouping],
        key ? markOf(key, grouping) : null,
        bands.get(key) ?? [],
      ),
    );
}

function band(
  key: string,
  label: string,
  mark: string | null,
  missions: RoadmapMissionResponse[],
): Band {
  return {
    key,
    label,
    mark,
    missions,
    speaking: missions.filter(speaks),
    silent: missions.filter((mission) => !speaks(mission)),
  };
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
 * What is folded away at the foot of a band.
 *
 * Composed here so a test can read it back: a French sentence built at run
 * time is invisible to the type checker, and a rename crossing it would only
 * show when somebody opened the page.
 */
export function silentNotice(count: number): string {
  return count > 1
    ? `${count} missions sans rien à montrer`
    : "1 mission sans rien à montrer";
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

/**
 * How far ahead a roadmap looks, in months.
 *
 * Nothing shorter than a quarter — below that one is reading a sprint, not a
 * road — and nothing longer than a year, past which a fortnight of work is
 * four pixels wide and the drawing says « somewhere in the spring ».
 *
 * The server throws in the month before on top, for context. It is not part
 * of the count: one asks how far ahead to look, not how wide the picture is.
 */
export const SPANS = [
  { months: 3, label: "3 mois" },
  { months: 6, label: "6 mois" },
  { months: 12, label: "12 mois" },
] as const;

export const DEFAULT_SPAN = 6;
