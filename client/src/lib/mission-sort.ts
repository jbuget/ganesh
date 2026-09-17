import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { PRIORITES, rangPhase } from "@/lib/board";

/** Les colonnes du referentiel sur lesquelles on peut ranger la liste. */
export type ColonneTri =
  "projet" | "phase" | "priorite" | "categorie" | "estime" | "realise";

export type SensTri = "asc" | "desc";

/** La colonne demandee, ou `null` pour l'ordre propre au referentiel. */
export interface TriMissions {
  colonne: ColonneTri | null;
  sens: SensTri;
}

export const AUCUN_TRI: TriMissions = { colonne: null, sens: "asc" };

const COLONNES: ColonneTri[] = [
  "projet",
  "phase",
  "priorite",
  "categorie",
  "estime",
  "realise",
];

const PARAMETRES = { colonne: "tri", sens: "sens" } as const;

const RANGS_PRIORITES = new Map(PRIORITES.map((p, rang) => [p.valeur, rang]));

type Mission = ProjectListItemResponse;

/**
 * Ce que chaque colonne donne a comparer.
 *
 * Une valeur absente vaut `null` : elle ne se compare pas, et le tri la range
 * en fin de liste plutot que de lui inventer un rang.
 */
const VALEURS: Record<ColonneTri, (m: Mission) => string | number | null> = {
  projet: (m) => m.project.label,
  phase: (m) => (m.project.statut ? rangPhase(m.project.statut) : null),
  priorite: (m) =>
    m.project.priorite ? (RANGS_PRIORITES.get(m.project.priorite) ?? null) : null,
  categorie: (m) => m.project.categorie,
  estime: (m) => m.project.estime_j ?? null,
  realise: (m) => m.realise_j,
};

function parLabel(a: Mission, b: Mission): number {
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
  const ecart = rangPhase(a.project.statut) - rangPhase(b.project.statut);
  return ecart !== 0 ? ecart : parLabel(a, b);
}

/**
 * Le comparateur a appliquer aux missions d'un meme niveau.
 *
 * Le sens ne renverse que la comparaison des valeurs : les missions sans
 * valeur restent en fin de liste, et deux missions qu'une colonne egalise
 * restent departagees par leur nom. Sans cela, inverser le sens ferait remonter
 * les trous en tete, et l'ordre des ex aequo changerait a chaque rendu.
 */
export function comparateurDeTri(tri: TriMissions) {
  if (tri.colonne === null) return parPhasePuisLabel;

  const valeurDe = VALEURS[tri.colonne];
  const signe = tri.sens === "desc" ? -1 : 1;

  return (a: Mission, b: Mission): number => {
    const gauche = valeurDe(a);
    const droite = valeurDe(b);

    if (gauche === null || droite === null) {
      if (gauche === droite) return parLabel(a, b);
      return gauche === null ? 1 : -1;
    }

    const ecart =
      typeof gauche === "string" && typeof droite === "string"
        ? gauche.localeCompare(droite, "fr")
        : Number(gauche) - Number(droite);

    return ecart !== 0 ? signe * ecart : parLabel(a, b);
  };
}

/**
 * Le tri obtenu en cliquant une colonne : croissant, decroissant, puis plus
 * rien. Le troisieme clic rend son ordre au referentiel, sans avoir a chercher
 * comment le retrouver.
 */
export function triSuivant(tri: TriMissions, colonne: ColonneTri): TriMissions {
  if (tri.colonne !== colonne) return { colonne, sens: "asc" };
  if (tri.sens === "asc") return { colonne, sens: "desc" };
  return AUCUN_TRI;
}

export function lireTri(params: URLSearchParams): TriMissions {
  const colonne = params.get(PARAMETRES.colonne);
  if (!colonne || !COLONNES.includes(colonne as ColonneTri)) return AUCUN_TRI;

  return {
    colonne: colonne as ColonneTri,
    sens: params.get(PARAMETRES.sens) === "desc" ? "desc" : "asc",
  };
}

/** Reporte le tri dans l'URL, sans toucher aux autres parametres. */
export function ecrireTri(params: URLSearchParams, tri: TriMissions): void {
  params.delete(PARAMETRES.colonne);
  params.delete(PARAMETRES.sens);
  if (tri.colonne === null) return;

  params.set(PARAMETRES.colonne, tri.colonne);
  params.set(PARAMETRES.sens, tri.sens);
}
