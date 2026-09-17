import type { ProjectCategory, ProjectStatus } from "@/lib/api/generated/model";

/** Phases du tableau, dans l'ordre des colonnes. */
export const PHASES: { statut: ProjectStatus; libelle: string }[] = [
  { statut: "exploration", libelle: "Exploration" },
  { statut: "cadrage", libelle: "Cadrage" },
  { statut: "realisation", libelle: "Réalisation" },
  { statut: "validation", libelle: "Validation" },
  { statut: "deploiement", libelle: "Déploiement" },
  { statut: "exploitation", libelle: "Exploitation" },
];

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
