import type {
  BoardMemberResponse,
  ProjectCategory,
  ProjectKind,
  ProjectPriority,
  ProjectResponse,
  ProjectStatus,
} from "@/lib/api/generated/model";
import { CATEGORIES, PHASES, PRIORITES } from "@/lib/board";

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
  intervenants: BoardMemberResponse[];
}

/** Ce que l'on demande a l'ecran de montrer. */
export interface MissionFilters {
  nom: string;
  phases: ProjectStatus[];
  categories: ProjectCategory[];
  priorites: ProjectPriority[];
  intervenants: number[];
  types: ProjectKind[];
  etats: EtatMission[];
}

/** Le tableau entier : aucun critere pose. */
export const AUCUN_FILTRE: MissionFilters = {
  nom: "",
  phases: [],
  categories: [],
  priorites: [],
  intervenants: [],
  types: [],
  etats: [],
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

/**
 * Les deux etats qu'une mission peut prendre.
 *
 * Ce critere est le seul dont le vide n'est pas neutre : le tableau sert a
 * piloter ce qui tourne, et montre donc les seules missions actives tant qu'on
 * ne demande pas les archivees.
 */
export const ETATS_DE_MISSION: { valeur: EtatMission; libelle: string }[] = [
  { valeur: "active", libelle: "Actives" },
  { valeur: "archivee", libelle: "Archivées" },
];

/** Minuscules et sans accent : on cherche « copropriete » et on trouve « copropriété ». */
function normaliser(texte: string): string {
  return texte
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

export function filtreActif(filtres: MissionFilters): boolean {
  return (
    filtres.nom.trim() !== "" ||
    filtres.phases.length > 0 ||
    filtres.categories.length > 0 ||
    filtres.priorites.length > 0 ||
    filtres.intervenants.length > 0 ||
    filtres.types.length > 0 ||
    filtres.etats.length > 0
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
function retenue(mission: FilterableMission, filtres: MissionFilters): boolean {
  const recherche = normaliser(filtres.nom.trim());
  if (recherche && !normaliser(mission.project.label).includes(recherche)) return false;

  if (filtres.phases.length > 0) {
    const phase = mission.project.statut;
    if (!phase || !filtres.phases.includes(phase)) return false;
  }

  const etat: EtatMission = mission.project.actif ? "active" : "archivee";
  if (!(filtres.etats.length > 0 ? filtres.etats : ["active"]).includes(etat)) {
    return false;
  }

  if (filtres.categories.length > 0) {
    const axe = mission.project.categorie;
    if (!axe || !filtres.categories.includes(axe)) return false;
  }

  if (filtres.priorites.length > 0) {
    const urgence = mission.project.priorite;
    if (!urgence || !filtres.priorites.includes(urgence)) return false;
  }

  if (filtres.types.length > 0 && !filtres.types.includes(mission.project.kind)) {
    return false;
  }

  if (filtres.intervenants.length > 0) {
    const porteurs = mission.intervenants.map((membre) => membre.id);
    if (!filtres.intervenants.some((id) => porteurs.includes(id))) return false;
  }

  return true;
}

export function filtrerMissions<T extends FilterableMission>(
  missions: T[],
  filtres: MissionFilters,
): T[] {
  return missions.filter((mission) => retenue(mission, filtres));
}

/**
 * Le tableau doit-il redemander les archivees au serveur ?
 *
 * Elles ne voyagent que sur demande : les charger pour les masquer aussitot
 * ferait payer a chaque ouverture du tableau ce dont on se sert rarement.
 */
export function inclutLesArchivees(filtres: MissionFilters): boolean {
  return filtres.etats.includes("archivee");
}

const PARAMETRES = {
  nom: "nom",
  phase: "phase",
  categorie: "categorie",
  priorite: "priorite",
  intervenant: "intervenant",
  type: "type",
  etat: "etat",
} as const;

const PHASES_CONNUES = new Set<string>(PHASES.map((p) => p.statut));
const CATEGORIES_CONNUES = new Set<string>(CATEGORIES.map((c) => c.valeur));
const PRIORITES_CONNUES = new Set<string>(PRIORITES.map((p) => p.valeur));
const TYPES_CONNUS = new Set<string>(TYPES_DE_MISSION.map((t) => t.valeur));
const ETATS_CONNUS = new Set<string>(ETATS_DE_MISSION.map((e) => e.valeur));

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
export function lireFiltres(params: URLSearchParams): MissionFilters {
  return {
    nom: params.get(PARAMETRES.nom) ?? "",
    phases: valeursConnues<ProjectStatus>(params, PARAMETRES.phase, PHASES_CONNUES),
    categories: valeursConnues<ProjectCategory>(
      params,
      PARAMETRES.categorie,
      CATEGORIES_CONNUES,
    ),
    priorites: valeursConnues<ProjectPriority>(
      params,
      PARAMETRES.priorite,
      PRIORITES_CONNUES,
    ),
    intervenants: params
      .getAll(PARAMETRES.intervenant)
      .map(Number)
      .filter((id) => Number.isInteger(id) && id > 0),
    types: valeursConnues<ProjectKind>(params, PARAMETRES.type, TYPES_CONNUS),
    etats: valeursConnues<EtatMission>(params, PARAMETRES.etat, ETATS_CONNUS),
  };
}

/** Reporte les filtres dans l'URL, sans toucher aux autres parametres. */
export function ecrireFiltres(params: URLSearchParams, filtres: MissionFilters): void {
  Object.values(PARAMETRES).forEach((nom) => params.delete(nom));

  if (filtres.nom.trim()) params.set(PARAMETRES.nom, filtres.nom.trim());
  filtres.phases.forEach((phase) => params.append(PARAMETRES.phase, phase));
  filtres.categories.forEach((axe) => params.append(PARAMETRES.categorie, axe));
  filtres.priorites.forEach((urgence) => params.append(PARAMETRES.priorite, urgence));
  filtres.intervenants.forEach((id) =>
    params.append(PARAMETRES.intervenant, String(id)),
  );
  filtres.types.forEach((type) => params.append(PARAMETRES.type, type));
  filtres.etats.forEach((etat) => params.append(PARAMETRES.etat, etat));
}
