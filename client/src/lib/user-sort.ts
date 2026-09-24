import type { UserResponse } from "@/lib/api/generated/model";
import { roleRank } from "@/lib/roles";
import {
  NO_COLUMN_SORT,
  compareValues,
  nextColumnSort,
  readColumnSort,
  writeColumnSort,
  type ColumnSort,
} from "@/lib/table-sort";

/** The team list columns the list can be ordered by. */
export type UserSortColumn = "name" | "email" | "github" | "role" | "login" | "status";

/** The column asked for, or `null` for the team list's own order. */
export type UserSort = ColumnSort<UserSortColumn>;

export const NO_USER_SORT: UserSort = NO_COLUMN_SORT;

const COLUMNS: UserSortColumn[] = [
  "name",
  "email",
  "github",
  "role",
  "login",
  "status",
];

/**
 * What each column gives to compare.
 *
 * A missing value is `null`: it does not compare, and the sort puts it at the
 * end of the list rather than inventing a rank for it. An account that never
 * came is the case that matters — « jamais » is not « il y a très longtemps »,
 * and must not take the top of a descending sort. A teammate with no GitHub
 * handle reads the same way: the « — » the row shows is not a name to sort.
 */
const VALUES: Record<UserSortColumn, (user: UserResponse) => string | number | null> = {
  name: (user) => user.display_name,
  email: (user) => user.email,
  github: (user) => user.github_username ?? null,
  // From the least to the most empowered, as the ladder declares them.
  role: (user) => roleRank(user.role),
  login: (user) => (user.last_login_at ? new Date(user.last_login_at).getTime() : null),
  status: (user) => (user.is_active ? 0 : 1),
};

function byName(a: UserResponse, b: UserResponse): number {
  return a.display_name.localeCompare(b.display_name, "fr");
}

/**
 * The team, arranged.
 *
 * With no column asked for, by name: in a list of people, the alphabet is the
 * only order one finds by eye. It is also what settles two rows a column cannot
 * separate — without it, two managers would swap places from one render to the
 * next.
 */
export function sortUsers(users: UserResponse[], sorted: UserSort): UserResponse[] {
  if (sorted.column === null) return [...users].sort(byName);

  const valueOf = VALUES[sorted.column];
  return [...users].sort((a, b) =>
    compareValues(a, b, valueOf, sorted.direction, byName),
  );
}

/**
 * The sort you get by clicking a column: ascending, descending, then nothing.
 * The third click gives the team list its own order back.
 */
export function nextUserSort(sorted: UserSort, column: UserSortColumn): UserSort {
  return nextColumnSort(sorted, column);
}

export function readUserSort(params: URLSearchParams): UserSort {
  return readColumnSort(params, COLUMNS);
}

/** Writes the sort into the URL, leaving the other parameters alone. */
export function writeUserSort(params: URLSearchParams, sorted: UserSort): void {
  writeColumnSort(params, sorted);
}
