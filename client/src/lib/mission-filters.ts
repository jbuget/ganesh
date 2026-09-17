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
 * Une mission est active tant qu'elle n'a pas ete archivee.
 *
 * L'archivage retire une mission des listes sans rien perdre de ce qui y a ete
 * declare : c'est ce qu'on fait d'un projet termine ou abandonne, quand la
 * suppression n'est plus possible.
 */
export type EtatMission = "active" | "archivee";

/**
 * Tout ce qui se filtre : une mission, et qui s'en occupe.
 *
 * La forme suffit a couvrir une carte du kanban comme une ligne du referentiel.
 * Les deux ecrans posent les memes questions au meme endroit, et une reponse
 * commune leur evite de diverger.
 */
export interface FilterableMission {
  project: ProjectResponse;
  contributors: BoardMemberResponse[];
}

/** Ce que l'on demande a l'ecran de montrer. */
export interface MissionFilters {
  name: string;
  phases: ProjectStatus[];
  categories: ProjectCategory[];
  priorities: ProjectPriority[];
  contributors: number[];
  types: ProjectKind[];
  states: EtatMission[];
}

/** Le tableau entier : aucun critere pose. */
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
 * Les deux natures qu'une carte peut prendre.
 *
 * Les activites hors projet n'apparaissent jamais sur le tableau : elles ne
 * portent pas de phase, et ce filtre ne les propose donc pas.
 */
export const MISSION_KINDS: { value: ProjectKind; label: string }[] = [
  { value: "project", label: "Projets" },
  { value: "work_package", label: "Sous-projets" },
];

/**
 * Les deux etats qu'une mission peut prendre.
 *
 * Ce critere est le seul dont le vide n'est pas neutre : le tableau sert a
 * piloter ce qui tourne, et montre donc les seules missions actives tant qu'on
 * ne demande pas les archivees.
 */
export const MISSION_STATES: { value: EtatMission; label: string }[] = [
  { value: "active", label: "Actives" },
  { value: "archivee", label: "Archivées" },
];

/** Minuscules et sans accent : on cherche « copropriete » et on trouve « copropriété ». */
function normalise(body: string): string {
  return body
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

export function filtreActif(filters: MissionFilters): boolean {
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
 * Une carte passe-t-elle les criteres ?
 *
 * Un critere vide ne retranche rien ; plusieurs valeurs dans un meme critere
 * s'additionnent, et les criteres entre eux se cumulent. « Realisation » et
 * « Nino » montre donc ce qui est en realisation *et* porte par Nino.
 *
 * Filtrer sur une phase vide les autres colonnes sans les retirer : le tableau
 * garde ses six phases d'un filtre a l'autre, et l'on continue de lire d'ou
 * viennent les cartes et ou elles vont.
 */
function kept(mission: FilterableMission, filters: MissionFilters): boolean {
  const search = normalise(filters.name.trim());
  if (search && !normalise(mission.project.label).includes(search)) return false;

  if (filters.phases.length > 0) {
    const phase = mission.project.status;
    if (!phase || !filters.phases.includes(phase)) return false;
  }

  const state: EtatMission = mission.project.is_active ? "active" : "archivee";
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
    const porteurs = mission.contributors.map((member) => member.id);
    if (!filters.contributors.some((id) => porteurs.includes(id))) return false;
  }

  return true;
}

export function filtrerMissions<T extends FilterableMission>(
  missions: T[],
  filters: MissionFilters,
): T[] {
  return missions.filter((mission) => kept(mission, filters));
}

/**
 * Le tableau doit-il redemander les archivees au serveur ?
 *
 * Elles ne voyagent que sur demande : les charger pour les masquer aussitot
 * ferait payer a chaque ouverture du tableau ce dont on se sert rarement.
 */
export function inclutLesArchivees(filters: MissionFilters): boolean {
  return filters.states.includes("archivee");
}

const PARAMETERS = {
  name: "name",
  phase: "phase",
  category: "categorie",
  priority: "priorite",
  contributor: "contributor",
  type: "type",
  state: "etat",
} as const;

const PHASES_CONNUES = new Set<string>(PHASES.map((p) => p.status));
const CATEGORIES_CONNUES = new Set<string>(CATEGORIES.map((c) => c.value));
const PRIORITES_CONNUES = new Set<string>(PRIORITIES.map((p) => p.value));
const TYPES_CONNUS = new Set<string>(MISSION_KINDS.map((t) => t.value));
const ETATS_CONNUS = new Set<string>(MISSION_STATES.map((e) => e.value));

/** Ne retient d'un parametre que les valeurs que l'on sait interpreter. */
function valeursConnues<T extends string>(
  params: URLSearchParams,
  name: string,
  known: Set<string>,
): T[] {
  return params.getAll(name).filter((value) => known.has(value)) as T[];
}

/**
 * Les filtres tels que l'URL les porte.
 *
 * Une valeur inconnue est ignoree : une adresse mal recopiee doit montrer le
 * tableau, pas un ecran vide sans explication.
 */
export function lireFiltres(params: URLSearchParams): MissionFilters {
  return {
    name: params.get(PARAMETERS.name) ?? "",
    phases: valeursConnues<ProjectStatus>(params, PARAMETERS.phase, PHASES_CONNUES),
    categories: valeursConnues<ProjectCategory>(
      params,
      PARAMETERS.category,
      CATEGORIES_CONNUES,
    ),
    priorities: valeursConnues<ProjectPriority>(
      params,
      PARAMETERS.priority,
      PRIORITES_CONNUES,
    ),
    contributors: params
      .getAll(PARAMETERS.contributor)
      .map(Number)
      .filter((id) => Number.isInteger(id) && id > 0),
    types: valeursConnues<ProjectKind>(params, PARAMETERS.type, TYPES_CONNUS),
    states: valeursConnues<EtatMission>(params, PARAMETERS.state, ETATS_CONNUS),
  };
}

/** Reporte les filtres dans l'URL, sans toucher aux autres parametres. */
export function ecrireFiltres(params: URLSearchParams, filters: MissionFilters): void {
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
