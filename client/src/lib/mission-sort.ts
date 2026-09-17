import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { PRIORITIES, phaseRank } from "@/lib/board";

/** Les colonnes du referentiel sur lesquelles on peut ranger la liste. */
export type SortColumn =
  "project" | "phase" | "priority" | "category" | "estimated" | "delivered";

export type SortDirection = "asc" | "desc";

/** La colonne demandee, ou `null` pour l'ordre propre au referentiel. */
export interface MissionSort {
  column: SortColumn | null;
  direction: SortDirection;
}

export const NO_SORT: MissionSort = { column: null, direction: "asc" };

const COLUMNS: SortColumn[] = [
  "project",
  "phase",
  "priority",
  "category",
  "estimated",
  "delivered",
];

const PARAMETERS = { column: "sort", direction: "direction" } as const;

const PRIORITY_RANKS = new Map(PRIORITIES.map((p, rang) => [p.value, rang]));

type Mission = ProjectListItemResponse;

/**
 * Ce que chaque colonne donne a comparer.
 *
 * Une valeur absente vaut `null` : elle ne se compare pas, et le tri la range
 * en fin de liste plutot que de lui inventer un rang.
 */
const VALUES: Record<SortColumn, (m: Mission) => string | number | null> = {
  project: (m) => m.project.label,
  phase: (m) => (m.project.status ? phaseRank(m.project.status) : null),
  priority: (m) =>
    m.project.priority ? (PRIORITY_RANKS.get(m.project.priority) ?? null) : null,
  category: (m) => m.project.category,
  estimated: (m) => m.project.estimated_days ?? null,
  delivered: (m) => m.delivered_days,
};

function byLabel(a: Mission, b: Mission): number {
  return a.project.label.localeCompare(b.project.label, "fr");
}

/**
 * Ou en est la mission d'abord, son nom ensuite.
 *
 * Le referentiel se parcourt comme le kanban se lit, de gauche a droite : ce
 * qui demarre en haut, ce qui tourne en bas. A phase egale, l'alphabet, seul
 * ordre ou l'on retrouve une mission dont on connait le nom.
 */
function parPhasePuisLabel(a: Mission, b: Mission): number {
  const ecart = phaseRank(a.project.status) - phaseRank(b.project.status);
  return ecart !== 0 ? ecart : byLabel(a, b);
}

/**
 * Le comparateur a appliquer aux missions d'un meme niveau.
 *
 * Le sens ne renverse que la comparaison des valeurs : les missions sans
 * valeur restent en fin de liste, et deux missions qu'une colonne egalise
 * restent departagees par leur nom. Sans cela, inverser le sens ferait remonter
 * les trous en tete, et l'ordre des ex aequo changerait a chaque rendu.
 */
export function comparateurDeTri(sorted: MissionSort) {
  if (sorted.column === null) return parPhasePuisLabel;

  const valeurDe = VALUES[sorted.column];
  const signe = sorted.direction === "desc" ? -1 : 1;

  return (a: Mission, b: Mission): number => {
    const gauche = valeurDe(a);
    const droite = valeurDe(b);

    if (gauche === null || droite === null) {
      if (gauche === droite) return byLabel(a, b);
      return gauche === null ? 1 : -1;
    }

    const ecart =
      typeof gauche === "string" && typeof droite === "string"
        ? gauche.localeCompare(droite, "fr")
        : Number(gauche) - Number(droite);

    return ecart !== 0 ? signe * ecart : byLabel(a, b);
  };
}

/**
 * Le tri obtenu en cliquant une colonne : croissant, decroissant, puis plus
 * rien. Le troisieme clic rend son ordre au referentiel, sans avoir a chercher
 * comment le retrouver.
 */
export function triSuivant(sorted: MissionSort, column: SortColumn): MissionSort {
  if (sorted.column !== column) return { column, direction: "asc" };
  if (sorted.direction === "asc") return { column, direction: "desc" };
  return NO_SORT;
}

export function readSort(params: URLSearchParams): MissionSort {
  const column = params.get(PARAMETERS.column);
  if (!column || !COLUMNS.includes(column as SortColumn)) return NO_SORT;

  return {
    column: column as SortColumn,
    direction: params.get(PARAMETERS.direction) === "desc" ? "desc" : "asc",
  };
}

/** Reporte le tri dans l'URL, sans toucher aux autres parametres. */
export function writeSort(params: URLSearchParams, sorted: MissionSort): void {
  params.delete(PARAMETERS.column);
  params.delete(PARAMETERS.direction);
  if (sorted.column === null) return;

  params.set(PARAMETERS.column, sorted.column);
  params.set(PARAMETERS.direction, sorted.direction);
}
