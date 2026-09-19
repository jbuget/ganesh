/**
 * Application wrappers around the hooks Orval generates.
 *
 * Orval types `data` as the union of the success and of the errors declared in
 * the OpenAPI. But `bffFetcher` raises an `ApiError` as soon as the response is
 * not 2xx: when a hook exposes data, it is always the success data. This file
 * is the only place that knowledge is applied, rather than scattering type
 * casts across the components.
 */
import { useGetMonthGrid } from "@/lib/api/generated/entries/entries";
import type {
  MonthGridResponse,
  MyMoodsResponse,
  PeriodRange,
  ProjectListItemResponse,
  StatisticsResponse,
  TeamMoodsResponse,
  UserResponse,
} from "@/lib/api/generated/model";
import { useGetMyMoods, useGetTeamMoods } from "@/lib/api/generated/moods/moods";
import { useGetStatistics } from "@/lib/api/generated/stats/stats";
import { useListProjects } from "@/lib/api/generated/projects/projects";
import { useGetMe, useListUsers } from "@/lib/api/generated/users/users";

function successOf<T>(response: { data: unknown } | undefined): T | undefined {
  return response?.data as T | undefined;
}

/** Same reasoning for the result of a mutation. */
export function mutationResult<T>(response: { data: unknown }): T {
  return response.data as T;
}

/** The current user. */
export function useCurrentUser() {
  const query = useGetMe();
  return { ...query, user: successOf<UserResponse>(query.data) };
}

/**
 * The teammates.
 *
 * Active ones only by default: anywhere other than the management screen, a
 * deactivated teammate has no business being offered.
 */
export function useTeammates(includeInactive = false) {
  const query = useListUsers(includeInactive ? { include_inactive: true } : undefined);
  return { ...query, teammates: successOf<UserResponse[]>(query.data) ?? [] };
}

/**
 * The mission reference list, each with who looks after it.
 *
 * Assignments come from the same request as the missions: the reference list
 * lines them up in columns, and one request per row would make them arrive one
 * after the other before the reader's eyes.
 *
 * Archived ones are only asked for when they are wanted: anywhere else, a
 * mission put away has no business being offered.
 */
export function useProjects(includeInactive = false) {
  const query = useListProjects(
    includeInactive ? { include_inactive: true } : undefined,
  );
  const missions = successOf<ProjectListItemResponse[]>(query.data) ?? [];
  return {
    ...query,
    missions,
    /** The missions alone, for screens that ignore assignments. */
    projects: missions.map((mission) => mission.project),
  };
}

/** A month's grid, for a given teammate. */
export function useMonthGrid(month: string, userId: number | null, enabled: boolean) {
  const query = useGetMonthGrid(
    { month, ...(userId ? { user_id: userId } : {}) },
    { query: { enabled } },
  );
  return { ...query, grid: successOf<MonthGridResponse>(query.data) };
}

/** The dashboard of one window. */
export function useStatistics(range: PeriodRange) {
  const query = useGetStatistics({ range });
  return { ...query, statistics: successOf<StatisticsResponse>(query.data) };
}

/** The days one may still answer for, and what one already said of them. */
export function useMyMoods() {
  const query = useGetMyMoods();
  return { ...query, days: successOf<MyMoodsResponse>(query.data)?.days ?? [] };
}

/** The team's morale over the last fortnight. */
export function useTeamMoods() {
  const query = useGetTeamMoods();
  return { ...query, window: successOf<TeamMoodsResponse>(query.data) };
}
