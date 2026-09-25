import type {
  Department,
  RequestResponse,
  RequestState,
} from "@/lib/api/generated/model";
import { REQUEST_STATES } from "@/lib/requests";
import { normalise } from "@/lib/search-text";

/** What the list of needs is asked to show. */
export interface RequestFilters {
  search: string;
  states: RequestState[];
  departments: Department[];
}

/**
 * What the screen opens on: the needs that still owe somebody something.
 *
 * The only criterion whose empty value is not neutral, and for the same
 * reason the team list leaves requesters out: one comes to this screen to
 * answer what is waiting, and a list opening on everything ever asked for
 * would bury the few that call for something today.
 *
 * The three states are three unfinished things, and none of them closes on
 * its own: one handed over waits to be weighed, one put off waits for the
 * moment to come — « plus tard » answers nothing, it postpones — and one
 * accepted waits to be built, since saying yes makes nothing exist. Each of
 * them, left out of sight, is a need nobody ever comes back to.
 *
 * What was refused, or built, is read by asking for it: those are settled.
 */
const WAITING: RequestState[] = ["submitted", "deferred", "accepted"];

export const NO_REQUEST_FILTER: RequestFilters = {
  search: "",
  states: WAITING,
  departments: [],
};

/** Nothing set at all: what « Effacer » leaves behind. */
export const EVERY_REQUEST: RequestFilters = {
  search: "",
  states: [],
  departments: [],
};

export function hasActiveRequestFilter(filters: RequestFilters): boolean {
  return (
    filters.search.trim() !== "" ||
    filters.states.length > 0 ||
    filters.departments.length > 0
  );
}

/**
 * Does a need pass the criteria?
 *
 * An empty criterion takes nothing away; several values within one criterion
 * add up, and criteria stack with each other. The search reads the title and
 * the name of whoever filed it: one looks a need up by whichever one has to
 * hand.
 */
function kept(request: RequestResponse, filters: RequestFilters): boolean {
  const search = normalise(filters.search.trim());
  if (
    search &&
    !normalise(request.title).includes(search) &&
    !normalise(request.requester.label).includes(search)
  ) {
    return false;
  }

  if (filters.states.length > 0 && !filters.states.includes(request.state)) {
    return false;
  }

  if (
    filters.departments.length > 0 &&
    !request.departments.some((department) => filters.departments.includes(department))
  ) {
    return false;
  }

  return true;
}

export function filterRequests(
  requests: RequestResponse[],
  filters: RequestFilters,
): RequestResponse[] {
  return requests.filter((request) => kept(request, filters));
}

const PARAMETERS = { search: "q", state: "state", department: "department" } as const;

const KNOWN_STATES = new Set<string>(REQUEST_STATES.map((state) => state.value));

/**
 * The filters as the URL carries them.
 *
 * An address that names no state opens on what is waiting, as the screen
 * does; `state=all` is how « every state » is written down, since an empty
 * list of states cannot be told from an absent one.
 */
export function readRequestFilters(params: URLSearchParams): RequestFilters {
  const states = params.getAll(PARAMETERS.state);
  return {
    search: params.get(PARAMETERS.search) ?? "",
    states: states.includes("all")
      ? []
      : states.length > 0
        ? (states.filter((value) => KNOWN_STATES.has(value)) as RequestState[])
        : WAITING,
    departments: params.getAll(PARAMETERS.department) as Department[],
  };
}

/** Writes the filters into the URL, leaving the other parameters alone. */
export function writeRequestFilters(
  params: URLSearchParams,
  filters: RequestFilters,
): void {
  Object.values(PARAMETERS).forEach((name) => params.delete(name));

  if (filters.search.trim()) params.set(PARAMETERS.search, filters.search.trim());
  if (filters.states.length === 0) params.set(PARAMETERS.state, "all");
  else filters.states.forEach((state) => params.append(PARAMETERS.state, state));
  filters.departments.forEach((department) =>
    params.append(PARAMETERS.department, department),
  );
}
