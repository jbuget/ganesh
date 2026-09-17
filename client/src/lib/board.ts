import type { ProjectCategory, ProjectStatus } from "@/lib/api/generated/model";

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

/** Date de mise en service, en toutes lettres et abregee. */
export function formatMiseEnService(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const [annee, mois, jour] = iso.split("-").map(Number);
  const MOIS = [
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
  ];
  return `${jour} ${MOIS[mois - 1]} ${annee}`;
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
