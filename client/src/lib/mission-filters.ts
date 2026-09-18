import type {
  BoardMemberResponse,
  ProjectCategory,
  ProjectKind,
  ProjectPriority,
  ProjectResponse,
  ProjectStatus,
} from "@/lib/api/generated/model";
import { CATEGORIES, PHASES, PRIORITIES } from "@/lib/board";

/**
 * A mission is active until it has been archived.
 *
 * Archiving takes a mission out of the lists without losing anything declared
 * on it: that is what becomes of a finished or abandoned project, when deleting
 * is no longer possible.
 */
export type MissionState = "active" | "archived";

/**
 * Everything that gets filtered: a mission, and who looks after it.
 *
 * The shape covers a kanban card as well as a reference list row. Both screens
 * ask the same questions in the same place, and a shared answer keeps them from
 * drifting apart.
 */
export interface FilterableMission {
  project: ProjectResponse;
  contributors: BoardMemberResponse[];
}

/** What the screen is asked to show. */
export interface MissionFilters {
  name: string;
  phases: ProjectStatus[];
  categories: ProjectCategory[];
  priorities: ProjectPriority[];
  contributors: number[];
  types: ProjectKind[];
  states: MissionState[];
}

/** The whole board: no criterion set. */
export const NO_FILTER: MissionFilters = {
  name: "",
  phases: [],
  categories: [],
  priorities: [],
  contributors: [],
  types: [],
  states: [],
};

/**
 * The two kinds a card can be.
 *
 * Off-project work never appears on the board: it carries no phase, so this
 * filter does not offer it.
 */
export const MISSION_KINDS: { value: ProjectKind; label: string }[] = [
  { value: "project", label: "Projets" },
  { value: "work_package", label: "Sous-projets" },
];

/**
 * The two states a mission can be in.
 *
 * This is the only criterion whose empty value is not neutral: the board is
 * there to steer what is running, and so shows active missions alone until the
 * archived ones are asked for.
 */
export const MISSION_STATES: { value: MissionState; label: string }[] = [
  { value: "active", label: "Actives" },
  { value: "archived", label: "Archivées" },
];

/** Lowercase and unaccented: searching « copropriete » finds « copropriété ». */
function normalise(body: string): string {
  return body
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

export function hasActiveFilter(filters: MissionFilters): boolean {
  return (
    filters.name.trim() !== "" ||
    filters.phases.length > 0 ||
    filters.categories.length > 0 ||
    filters.priorities.length > 0 ||
    filters.contributors.length > 0 ||
    filters.types.length > 0 ||
    filters.states.length > 0
  );
}

/**
 * Does a card pass the criteria?
 *
 * An empty criterion takes nothing away; several values within one criterion
 * add up, and criteria stack with each other. « Réalisation » and
 * « Nino » therefore shows what is in development *and* carried by Nino.
 *
 * Filtering on a phase empties the other columns without removing them: the
 * board keeps its six phases from one filter to the next, and one goes on
 * reading where cards come from and where they go.
 */
function kept(mission: FilterableMission, filters: MissionFilters): boolean {
  const search = normalise(filters.name.trim());
  if (search && !normalise(mission.project.label).includes(search)) return false;

  if (filters.phases.length > 0) {
    const phase = mission.project.status;
    if (!phase || !filters.phases.includes(phase)) return false;
  }

  const state: MissionState = mission.project.is_active ? "active" : "archived";
  if (!(filters.states.length > 0 ? filters.states : ["active"]).includes(state)) {
    return false;
  }

  if (filters.categories.length > 0) {
    const axis = mission.project.category;
    if (!axis || !filters.categories.includes(axis)) return false;
  }

  if (filters.priorities.length > 0) {
    const urgency = mission.project.priority;
    if (!urgency || !filters.priorities.includes(urgency)) return false;
  }

  if (filters.types.length > 0 && !filters.types.includes(mission.project.kind)) {
    return false;
  }

  if (filters.contributors.length > 0) {
    const holders = mission.contributors.map((member) => member.id);
    if (!filters.contributors.some((id) => holders.includes(id))) return false;
  }

  return true;
}

export function filterMissions<T extends FilterableMission>(
  missions: T[],
  filters: MissionFilters,
): T[] {
  return missions.filter((mission) => kept(mission, filters));
}

/**
 * Should the board ask the server for the archived ones again?
 *
 * They only travel on request: loading them to hide them straight away would
 * make every opening of the board pay for what is rarely used.
 */
export function includesArchived(filters: MissionFilters): boolean {
  return filters.states.includes("archived");
}

const PARAMETERS = {
  name: "name",
  phase: "phase",
  category: "category",
  priority: "priority",
  contributor: "contributor",
  type: "type",
  state: "state",
} as const;

const KNOWN_PHASES = new Set<string>(PHASES.map((p) => p.status));
const KNOWN_CATEGORIES = new Set<string>(CATEGORIES.map((c) => c.value));
const KNOWN_PRIORITIES = new Set<string>(PRIORITIES.map((p) => p.value));
const KNOWN_KINDS = new Set<string>(MISSION_KINDS.map((t) => t.value));
const KNOWN_STATES = new Set<string>(MISSION_STATES.map((e) => e.value));

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
 * An unknown value is ignored: a mistyped address must show the board, not an
 * empty screen with no explanation.
 */
export function readFilters(params: URLSearchParams): MissionFilters {
  return {
    name: params.get(PARAMETERS.name) ?? "",
    phases: knownValues<ProjectStatus>(params, PARAMETERS.phase, KNOWN_PHASES),
    categories: knownValues<ProjectCategory>(
      params,
      PARAMETERS.category,
      KNOWN_CATEGORIES,
    ),
    priorities: knownValues<ProjectPriority>(
      params,
      PARAMETERS.priority,
      KNOWN_PRIORITIES,
    ),
    contributors: params
      .getAll(PARAMETERS.contributor)
      .map(Number)
      .filter((id) => Number.isInteger(id) && id > 0),
    types: knownValues<ProjectKind>(params, PARAMETERS.type, KNOWN_KINDS),
    states: knownValues<MissionState>(params, PARAMETERS.state, KNOWN_STATES),
  };
}

/** Writes the filters into the URL, leaving the other parameters alone. */
export function writeFilters(params: URLSearchParams, filters: MissionFilters): void {
  Object.values(PARAMETERS).forEach((name) => params.delete(name));

  if (filters.name.trim()) params.set(PARAMETERS.name, filters.name.trim());
  filters.phases.forEach((phase) => params.append(PARAMETERS.phase, phase));
  filters.categories.forEach((axis) => params.append(PARAMETERS.category, axis));
  filters.priorities.forEach((urgency) => params.append(PARAMETERS.priority, urgency));
  filters.contributors.forEach((id) =>
    params.append(PARAMETERS.contributor, String(id)),
  );
  filters.types.forEach((type) => params.append(PARAMETERS.type, type));
  filters.states.forEach((state) => params.append(PARAMETERS.state, state));
}
