import type {
  MonthGridResponse,
  ProjectListItemResponse,
} from "@/lib/api/generated/model";
import { phaseRank } from "@/lib/board";
import type { MonthCursor } from "@/lib/dates";

/**
 * A mission the home screen shows, with what one put on it this month.
 *
 * The listed item is kept whole rather than its project alone: the card reads
 * the phase and the urgency from it, and the news feed reads the thread from
 * the same object — one definition of « my missions » for both.
 */
export interface HomeMission {
  item: ProjectListItemResponse;
  /** Days declared on it this month, forecast included. */
  days: number;
  /** Whether the team put one on it, as opposed to having only logged time. */
  isContributor: boolean;
  /** What a work package hangs from: « Lot 2 » alone names nothing. */
  parentLabel: string | null;
}

/** A month gone by that is still waiting for something. */
export interface OpenMonth extends MonthCursor {
  /** Nothing was ever entered on it, forecast included. */
  isEmpty: boolean;
}

/**
 * The months gone by that are still open, in the order they are given.
 *
 * A month is open until someone validates it, and the two ways of leaving one
 * behind are told apart: never filled in, or filled in and never closed. They
 * call for different gestures, so the screen must not word them the same.
 *
 * A month never touched carries no record of its own and reads as open, which
 * is what one wants: a month one forgot entirely is exactly the one to be
 * reminded of.
 */
export function monthsToSettle(
  months: { cursor: MonthCursor; grid: MonthGridResponse | undefined }[],
): OpenMonth[] {
  return months.flatMap(({ cursor, grid }) =>
    grid?.is_writable
      ? [{ ...cursor, isEmpty: grid.actual_total + grid.forecast_total === 0 }]
      : [],
  );
}

/** One piece of news, and the mission it speaks of. */
export interface HomeUpdate {
  item: ProjectListItemResponse;
  update: NonNullable<ProjectListItemResponse["latest_update"]>;
}

/**
 * Working days already gone by with nothing entered on them.
 *
 * Today is left out on purpose: a day under way is not a gap, and naming it
 * would put a warning on the screen every morning. Non-working days are left
 * out because nothing may be written on them at all.
 */
export function daysMissingEntry(
  grid: MonthGridResponse | undefined,
  today: string,
): string[] {
  if (!grid) return [];

  const entered = new Map(grid.day_totals.map((day) => [day.day, day.total]));

  return grid.days
    .filter((day) => !day.is_off_day && day.day < today)
    .filter((day) => (entered.get(day.day) ?? 0) === 0)
    .map((day) => day.day);
}

/** Missions carrying time in a month, those merely lined up excluded. */
function worked(grid: MonthGridResponse | undefined): Set<number> {
  const ids = (grid?.rows ?? [])
    .filter((row) => row.total > 0)
    .map((row) => row.project_id);
  return new Set(ids);
}

/**
 * The missions one works on: those the team put one on, and those one has
 * spent days on lately.
 *
 * Contributors say what holds today — the field is settled week by week, and
 * carries no history — so they alone would miss a mission left last month and
 * still worth reading. The two months already loaded by the screen close that
 * gap without a request of their own.
 *
 * A row lined up on the month with nothing entered does not count: it says
 * « about to », not « working on », and the screen already names that elsewhere.
 *
 * Being a lead does not count either, as everywhere else in the application:
 * answering for a mission's choices is not spending days on it.
 *
 * Sorted by what takes the most time this month, then by the phase order of
 * the board: two missions at zero turn up in the order one steers them.
 */
export function myMissions(
  missions: ProjectListItemResponse[],
  userId: number | null,
  currentGrid: MonthGridResponse | undefined,
  previousGrid: MonthGridResponse | undefined,
): HomeMission[] {
  if (userId === null) return [];

  const thisMonth = worked(currentGrid);
  const lastMonth = worked(previousGrid);
  const days = new Map(
    (currentGrid?.rows ?? []).map((row) => [row.project_id, row.total]),
  );
  const labels = new Map(missions.map(({ project }) => [project.id, project.label]));

  return missions
    .map((item) => ({
      item,
      days: days.get(item.project.id) ?? 0,
      isContributor: item.contributors.some((member) => member.id === userId),
      parentLabel: item.project.parent_id
        ? (labels.get(item.project.parent_id) ?? null)
        : null,
    }))
    .filter(
      (mission) =>
        mission.isContributor ||
        thisMonth.has(mission.item.project.id) ||
        lastMonth.has(mission.item.project.id),
    )
    .sort(
      (a, b) =>
        b.days - a.days ||
        phaseRank(a.item.project.status) - phaseRank(b.item.project.status) ||
        a.item.project.label.localeCompare(b.item.project.label),
    );
}

/**
 * The latest news published on one's missions, the most recent first.
 *
 * One entry per mission: the list only carries the last message of each
 * thread, and the feed says what is new rather than replaying a conversation.
 */
export function latestUpdates(mine: HomeMission[], limit: number): HomeUpdate[] {
  return mine
    .flatMap((mission) =>
      mission.item.latest_update
        ? [{ item: mission.item, update: mission.item.latest_update }]
        : [],
    )
    .sort((a, b) => b.update.published_at.localeCompare(a.update.published_at))
    .slice(0, limit);
}
