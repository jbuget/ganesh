import type {
  ProjectCategory,
  ProjectPriority,
  ProjectStatus,
} from "@/lib/api/generated/model";

/**
 * Phases du tableau, dans l'ordre des colonnes.
 *
 * La pastille suit l'avancement, du gris de ce qui n'est pas commence au vert
 * de ce qui tourne : la couleur situe une colonne avant meme d'en lire le titre.
 */
export const PHASES: { statut: ProjectStatus; libelle: string; pastille: string }[] = [
  { statut: "exploration", libelle: "Exploration", pastille: "bg-slate-400" },
  { statut: "cadrage", libelle: "Cadrage", pastille: "bg-violet-500" },
  { statut: "realisation", libelle: "Réalisation", pastille: "bg-blue-500" },
  { statut: "validation", libelle: "Validation", pastille: "bg-amber-500" },
  { statut: "deploiement", libelle: "Déploiement", pastille: "bg-orange-500" },
  { statut: "exploitation", libelle: "Exploitation", pastille: "bg-emerald-500" },
];

const PHASES_PAR_STATUT = new Map(PHASES.map((p) => [p.statut, p]));

/** Couleur de la pastille d'une phase. */
export function pastillePhase(statut: ProjectStatus): string {
  return PHASES_PAR_STATUT.get(statut)?.pastille ?? "bg-slate-300";
}

const RANGS_PHASES = new Map(PHASES.map((phase, rang) => [phase.statut, rang]));

/**
 * Rang d'une phase dans le cycle de vie.
 *
 * Donne aux listes le meme ordre que les colonnes du kanban : on retrouve une
 * mission au meme endroit relatif, quel que soit l'ecran. Ce qui ne porte pas
 * de phase ferme la marche plutot que d'ouvrir le bal.
 */
export function rangPhase(statut: ProjectStatus | null | undefined): number {
  return statut ? (RANGS_PHASES.get(statut) ?? PHASES.length) : PHASES.length;
}

const LIBELLES_PHASES = new Map(PHASES.map((p) => [p.statut, p.libelle]));

export function libellePhase(statut: ProjectStatus): string {
  return LIBELLES_PHASES.get(statut) ?? statut;
}

/** Axes strategiques, avec la teinte qui les distingue sur une carte. */
export const CATEGORIES: {
  valeur: ProjectCategory;
  libelle: string;
  classe: string;
}[] = [
  {
    valeur: "automatiser_fluidifier",
    libelle: "Automatiser & fluidifier",
    classe: "bg-sky-100 text-sky-900",
  },
  {
    valeur: "perenniser_croissance",
    libelle: "Pérenniser la croissance",
    classe: "bg-emerald-100 text-emerald-900",
  },
  {
    valeur: "innover_differencier",
    libelle: "Innover & différencier",
    classe: "bg-violet-100 text-violet-900",
  },
  {
    valeur: "structurer_plateforme",
    libelle: "Structurer la plateforme",
    classe: "bg-amber-100 text-amber-900",
  },
];

const CATEGORIES_PAR_VALEUR = new Map(CATEGORIES.map((c) => [c.valeur, c]));

export function categorie(valeur: ProjectCategory | null | undefined) {
  return valeur ? (CATEGORIES_PAR_VALEUR.get(valeur) ?? null) : null;
}

/**
 * Urgences, de la plus forte a la plus faible.
 *
 * La couleur est pleine, la ou les axes strategiques restent en pastel : une
 * priorite doit sauter aux yeux d'un bout a l'autre du tableau, un axe se lit
 * quand on s'arrete sur une carte.
 */
export const PRIORITES: {
  valeur: ProjectPriority;
  libelle: string;
  classe: string;
  pastille: string;
}[] = [
  {
    valeur: "critique",
    libelle: "Critique",
    classe: "bg-slate-900 text-white",
    pastille: "bg-slate-900",
  },
  {
    valeur: "haute",
    libelle: "Haute",
    classe: "bg-red-600 text-white",
    pastille: "bg-red-600",
  },
  {
    valeur: "normale",
    libelle: "Normale",
    classe: "bg-orange-500 text-white",
    pastille: "bg-orange-500",
  },
  {
    valeur: "basse",
    libelle: "Basse",
    classe: "bg-amber-300 text-amber-950",
    pastille: "bg-amber-300",
  },
];

const PRIORITES_PAR_VALEUR = new Map(PRIORITES.map((p) => [p.valeur, p]));

export function priorite(valeur: ProjectPriority | null | undefined) {
  return valeur ? (PRIORITES_PAR_VALEUR.get(valeur) ?? null) : null;
}

/** Etat d'avancement d'une mission par rapport a son estime. */
export type Avancement = "sans-estime" | "en-cours" | "proche" | "depasse";

export function avancement(
  consomme: number,
  estime: number | null | undefined,
): Avancement {
  if (!estime) return "sans-estime";
  const part = consomme / estime;
  if (part > 1) return "depasse";
  if (part >= 0.8) return "proche";
  return "en-cours";
}
