import type {
  BoardCardResponse,
  ProjectCategory,
  ProjectKind,
  ProjectStatus,
} from "@/lib/api/generated/model";
import { CATEGORIES, PHASES } from "@/lib/board";

/** Ce que l'on demande au tableau de montrer. */
export interface BoardFilters {
  nom: string;
  phases: ProjectStatus[];
  categories: ProjectCategory[];
  intervenants: number[];
  types: ProjectKind[];
}

/** Le tableau entier : aucun critere pose. */
export const AUCUN_FILTRE: BoardFilters = {
  nom: "",
  phases: [],
  categories: [],
  intervenants: [],
  types: [],
};

/**
 * Les deux natures qu'une carte peut prendre.
 *
 * Les activites hors projet n'apparaissent jamais sur le tableau : elles ne
 * portent pas de phase, et ce filtre ne les propose donc pas.
 */
export const TYPES_DE_MISSION: { valeur: ProjectKind; libelle: string }[] = [
  { valeur: "projet", libelle: "Projets" },
  { valeur: "lot", libelle: "Sous-projets" },
];

/** Minuscules et sans accent : on cherche « copropriete » et on trouve « copropriété ». */
function normaliser(texte: string): string {
  return texte
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

export function filtreActif(filtres: BoardFilters): boolean {
  return (
    filtres.nom.trim() !== "" ||
    filtres.phases.length > 0 ||
    filtres.categories.length > 0 ||
    filtres.intervenants.length > 0 ||
    filtres.types.length > 0
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
function retientLaCarte(carte: BoardCardResponse, filtres: BoardFilters): boolean {
  const recherche = normaliser(filtres.nom.trim());
  if (recherche && !normaliser(carte.project.label).includes(recherche)) return false;

  if (filtres.phases.length > 0) {
    const phase = carte.project.statut;
    if (!phase || !filtres.phases.includes(phase)) return false;
  }

  if (filtres.categories.length > 0) {
    const axe = carte.project.categorie;
    if (!axe || !filtres.categories.includes(axe)) return false;
  }

  if (filtres.types.length > 0 && !filtres.types.includes(carte.project.kind)) {
    return false;
  }

  if (filtres.intervenants.length > 0) {
    const porteurs = carte.intervenants.map((membre) => membre.id);
    if (!filtres.intervenants.some((id) => porteurs.includes(id))) return false;
  }

  return true;
}

export function filtrerCartes(
  cartes: BoardCardResponse[],
  filtres: BoardFilters,
): BoardCardResponse[] {
  return cartes.filter((carte) => retientLaCarte(carte, filtres));
}

const PARAMETRES = {
  nom: "nom",
  phase: "phase",
  categorie: "categorie",
  intervenant: "intervenant",
  type: "type",
} as const;

const PHASES_CONNUES = new Set<string>(PHASES.map((p) => p.statut));
const CATEGORIES_CONNUES = new Set<string>(CATEGORIES.map((c) => c.valeur));
const TYPES_CONNUS = new Set<string>(TYPES_DE_MISSION.map((t) => t.valeur));

/** Ne retient d'un parametre que les valeurs que l'on sait interpreter. */
function valeursConnues<T extends string>(
  params: URLSearchParams,
  nom: string,
  connues: Set<string>,
): T[] {
  return params.getAll(nom).filter((valeur) => connues.has(valeur)) as T[];
}

/**
 * Les filtres tels que l'URL les porte.
 *
 * Une valeur inconnue est ignoree : une adresse mal recopiee doit montrer le
 * tableau, pas un ecran vide sans explication.
 */
export function lireFiltres(params: URLSearchParams): BoardFilters {
  return {
    nom: params.get(PARAMETRES.nom) ?? "",
    phases: valeursConnues<ProjectStatus>(params, PARAMETRES.phase, PHASES_CONNUES),
    categories: valeursConnues<ProjectCategory>(
      params,
      PARAMETRES.categorie,
      CATEGORIES_CONNUES,
    ),
    intervenants: params
      .getAll(PARAMETRES.intervenant)
      .map(Number)
      .filter((id) => Number.isInteger(id) && id > 0),
    types: valeursConnues<ProjectKind>(params, PARAMETRES.type, TYPES_CONNUS),
  };
}

/** Reporte les filtres dans l'URL, sans toucher aux autres parametres. */
export function ecrireFiltres(params: URLSearchParams, filtres: BoardFilters): void {
  Object.values(PARAMETRES).forEach((nom) => params.delete(nom));

  if (filtres.nom.trim()) params.set(PARAMETRES.nom, filtres.nom.trim());
  filtres.phases.forEach((phase) => params.append(PARAMETRES.phase, phase));
  filtres.categories.forEach((axe) => params.append(PARAMETRES.categorie, axe));
  filtres.intervenants.forEach((id) =>
    params.append(PARAMETRES.intervenant, String(id)),
  );
  filtres.types.forEach((type) => params.append(PARAMETRES.type, type));
}
