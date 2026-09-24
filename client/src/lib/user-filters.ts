import type { Role, UserResponse } from "@/lib/api/generated/model";
import { ROLES } from "@/lib/roles";
import { normalise } from "@/lib/search-text";

/**
 * A teammate's access is open until it has been cut off.
 *
 * Deactivating takes an account out of the list without losing what it has
 * declared: that is what becomes of someone who has left, when deleting is no
 * longer possible.
 */
export type UserState = "active" | "inactive";

/** What the team list is asked to show. */
export interface UserFilters {
  name: string;
  roles: Role[];
  states: UserState[];
}

/** The whole team: no criterion set. */
export const NO_USER_FILTER: UserFilters = {
  name: "",
  roles: [],
  states: [],
};

/**
 * The two states an account can be in.
 *
 * This is the only criterion whose empty value is not neutral: the list is
 * there to show who is on the team, and so shows open accounts alone until the
 * deactivated ones are asked for. It replaces the switch the screen used to
 * carry, and says the same thing in the vocabulary of the other criteria.
 */
export const USER_STATES: { value: UserState; label: string }[] = [
  { value: "active", label: "Actifs" },
  { value: "inactive", label: "Désactivés" },
];

export function hasActiveUserFilter(filters: UserFilters): boolean {
  return (
    filters.name.trim() !== "" || filters.roles.length > 0 || filters.states.length > 0
  );
}

/**
 * The roles the list is about.
 *
 * Like the state, the empty role criterion is not neutral: everybody at WAAT
 * signs in through the same tenant, so the list would otherwise fill up with
 * three hundred accounts of people who are not on the team. Guests are shown
 * when they are asked for, and not before.
 */
const TEAM_ROLES: Role[] = ["TEAMMATE", "MANAGER", "ADMIN"];

/**
 * Does a teammate pass the criteria?
 *
 * An empty criterion takes nothing away — bar the two whose empty value says
 * something, the state and the role; several values within one criterion add
 * up, and criteria stack with each other. « Manager » and « che » therefore
 * shows the managers *whose name is being searched*.
 *
 * The search reads the name and the email: one looks a colleague up by
 * whichever one has to hand.
 */
function kept(user: UserResponse, filters: UserFilters): boolean {
  const search = normalise(filters.name.trim());
  if (
    search &&
    !normalise(user.display_name).includes(search) &&
    !normalise(user.email).includes(search)
  ) {
    return false;
  }

  const state: UserState = user.is_active ? "active" : "inactive";
  if (!(filters.states.length > 0 ? filters.states : ["active"]).includes(state)) {
    return false;
  }

  const roles = filters.roles.length > 0 ? filters.roles : TEAM_ROLES;
  if (!roles.includes(user.role)) return false;

  return true;
}

export function filterUsers(
  users: UserResponse[],
  filters: UserFilters,
): UserResponse[] {
  return users.filter((user) => kept(user, filters));
}

/**
 * How many guests the criteria are keeping out of sight.
 *
 * The list hides them by default and would otherwise say nothing of it: on a
 * screen showing fifteen rows out of three hundred, that silence is what
 * makes somebody look for an account they were never shown. The other
 * criteria still apply — a search for « chen » counts the guests named Chen,
 * and no others — so the figure is what one more click would actually bring.
 */
export function hiddenGuests(users: UserResponse[], filters: UserFilters): number {
  if (filters.roles.includes("GUEST")) return 0;
  return filterUsers(users, { ...filters, roles: ["GUEST"] }).length;
}

/**
 * The same question, asked with the guests in sight.
 *
 * The empty role criterion means « the team », so it is written out before
 * the guests are added to it: setting « GUEST » alone would show them
 * *instead of* the team, which is not what somebody clicking « afficher »
 * asked for.
 */
export function withGuests(filters: UserFilters): UserFilters {
  const shown = filters.roles.length > 0 ? filters.roles : TEAM_ROLES;
  return { ...filters, roles: [...shown, "GUEST"] };
}

const PARAMETERS = { name: "name", role: "role", state: "state" } as const;

const KNOWN_ROLES = new Set<string>(ROLES.map((role) => role.value));
const KNOWN_STATES = new Set<string>(USER_STATES.map((state) => state.value));

/** Keeps from a parameter only the values we know how to read. */
function knownValues<T extends string>(
  params: URLSearchParams,
  name: string,
  known: Set<string>,
): T[] {
  return params.getAll(name).filter((value) => known.has(value)) as T[];
}

/**
 * The filters as the URL carries them.
 *
 * An unknown value is ignored: a mistyped address must show the team, not an
 * empty screen with no explanation.
 */
export function readUserFilters(params: URLSearchParams): UserFilters {
  return {
    name: params.get(PARAMETERS.name) ?? "",
    roles: knownValues<Role>(params, PARAMETERS.role, KNOWN_ROLES),
    states: knownValues<UserState>(params, PARAMETERS.state, KNOWN_STATES),
  };
}

/** Writes the filters into the URL, leaving the other parameters alone. */
export function writeUserFilters(params: URLSearchParams, filters: UserFilters): void {
  Object.values(PARAMETERS).forEach((name) => params.delete(name));

  if (filters.name.trim()) params.set(PARAMETERS.name, filters.name.trim());
  filters.roles.forEach((role) => params.append(PARAMETERS.role, role));
  filters.states.forEach((state) => params.append(PARAMETERS.state, state));
}
