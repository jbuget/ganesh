import { Signal, SignalHigh, SignalLow, SignalMedium } from "lucide-react";
import type { LucideIcon } from "lucide-react";

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

/**
 * Axes strategiques, avec la teinte qui les distingue.
 *
 * Meme grammaire que les phases et les urgences : une marque coloree, un
 * libelle ordinaire. La marque est carree, la ou celle d'une phase est ronde :
 * deux points de meme forme sur une meme ligne se confondraient.
 */
export const CATEGORIES: {
  valeur: ProjectCategory;
  libelle: string;
  puce: string;
}[] = [
  {
    valeur: "automatiser_fluidifier",
    libelle: "Automatiser & fluidifier",
    puce: "bg-sky-500",
  },
  {
    valeur: "perenniser_croissance",
    libelle: "Pérenniser la croissance",
    puce: "bg-emerald-500",
  },
  {
    valeur: "innover_differencier",
    libelle: "Innover & différencier",
    puce: "bg-violet-500",
  },
  {
    valeur: "structurer_plateforme",
    libelle: "Structurer la plateforme",
    puce: "bg-amber-500",
  },
];

const CATEGORIES_PAR_VALEUR = new Map(CATEGORIES.map((c) => [c.valeur, c]));

export function categorie(valeur: ProjectCategory | null | undefined) {
  return valeur ? (CATEGORIES_PAR_VALEUR.get(valeur) ?? null) : null;
}

/**
 * Urgences, de la plus forte a la plus faible.
 *
 * Une marque coloree et un libelle en texte ordinaire, comme les phases : la
 * couleur repere, elle ne remplit pas. Trois surfaces teintees par ligne — une
 * par phase, une par urgence, une par axe — faisaient crier les deux colonnes
 * les moins structurantes plus fort que le nom de la mission.
 *
 * L'echelle se lit au remplissage — quatre barres, puis trois, deux, une —
 * et pas seulement a la teinte : elle reste donc lisible pour qui ne distingue
 * pas les couleurs, ou n'en dispose pas.
 */
export const PRIORITES: {
  valeur: ProjectPriority;
  libelle: string;
  icone: LucideIcon;
  couleur: string;
}[] = [
  { valeur: "critique", libelle: "Critique", icone: Signal, couleur: "text-red-600" },
  { valeur: "haute", libelle: "Haute", icone: SignalHigh, couleur: "text-orange-500" },
  {
    valeur: "normale",
    libelle: "Normale",
    icone: SignalMedium,
    couleur: "text-amber-500",
  },
  // Une priorite basse n'a pas a attirer le regard : le gris la fait reculer,
  // et l'oeil ne retient que ce qui demande une decision.
  { valeur: "basse", libelle: "Basse", icone: SignalLow, couleur: "text-slate-400" },
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
