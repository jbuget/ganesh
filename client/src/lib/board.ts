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
export const PHASES: { status: ProjectStatus; label: string; dot: string }[] = [
  { status: "exploration", label: "Exploration", dot: "bg-slate-400" },
  { status: "scoping", label: "Cadrage", dot: "bg-violet-500" },
  { status: "build", label: "Réalisation", dot: "bg-blue-500" },
  { status: "validation", label: "Validation", dot: "bg-amber-500" },
  { status: "deployment", label: "Déploiement", dot: "bg-orange-500" },
  { status: "operations", label: "Exploitation", dot: "bg-emerald-500" },
];

const PHASES_PAR_STATUT = new Map(PHASES.map((p) => [p.status, p]));

/** Couleur de la pastille d'une phase. */
export function phaseDot(status: ProjectStatus): string {
  return PHASES_PAR_STATUT.get(status)?.dot ?? "bg-slate-300";
}

const RANGS_PHASES = new Map(PHASES.map((phase, rang) => [phase.status, rang]));

/**
 * Rang d'une phase dans le cycle de vie.
 *
 * Donne aux listes le meme ordre que les colonnes du kanban : on retrouve une
 * mission au meme endroit relatif, quel que soit l'ecran. Ce qui ne porte pas
 * de phase ferme la marche plutot que d'ouvrir le bal.
 */
export function phaseRank(status: ProjectStatus | null | undefined): number {
  return status ? (RANGS_PHASES.get(status) ?? PHASES.length) : PHASES.length;
}

const LIBELLES_PHASES = new Map(PHASES.map((p) => [p.status, p.label]));

export function phaseLabel(status: ProjectStatus): string {
  return LIBELLES_PHASES.get(status) ?? status;
}

/**
 * Axes strategiques, avec la teinte qui les distingue.
 *
 * Meme grammaire que les phases et les urgences : une marque coloree, un
 * libelle ordinaire. La marque est carree, la ou celle d'une phase est ronde :
 * deux points de meme forme sur une meme ligne se confondraient.
 */
export const CATEGORIES: {
  value: ProjectCategory;
  label: string;
  bullet: string;
}[] = [
  {
    value: "automate_streamline",
    label: "Automatiser & fluidifier",
    bullet: "bg-sky-500",
  },
  {
    value: "sustain_growth",
    label: "Pérenniser la croissance",
    bullet: "bg-emerald-500",
  },
  {
    value: "innovate_differentiate",
    label: "Innover & différencier",
    bullet: "bg-violet-500",
  },
  {
    value: "structure_platform",
    label: "Structurer la plateforme",
    bullet: "bg-amber-500",
  },
];

const CATEGORIES_PAR_VALEUR = new Map(CATEGORIES.map((c) => [c.value, c]));

export function category(value: ProjectCategory | null | undefined) {
  return value ? (CATEGORIES_PAR_VALEUR.get(value) ?? null) : null;
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
export const PRIORITIES: {
  value: ProjectPriority;
  label: string;
  icon: LucideIcon;
  colour: string;
}[] = [
  { value: "critical", label: "Critique", icon: Signal, colour: "text-red-600" },
  { value: "high", label: "Haute", icon: SignalHigh, colour: "text-orange-500" },
  {
    value: "normal",
    label: "Normale",
    icon: SignalMedium,
    colour: "text-amber-500",
  },
  // Une priorite basse n'a pas a attirer le regard : le gris la fait reculer,
  // et l'oeil ne retient que ce qui demande une decision.
  { value: "low", label: "Basse", icon: SignalLow, colour: "text-slate-400" },
];

const PRIORITES_PAR_VALEUR = new Map(PRIORITIES.map((p) => [p.value, p]));

export function priority(value: ProjectPriority | null | undefined) {
  return value ? (PRIORITES_PAR_VALEUR.get(value) ?? null) : null;
}

/** Etat d'avancement d'une mission par rapport a son estime. */
export type Avancement = "sans-estime" | "en-cours" | "proche" | "depasse";

export function progress(
  consomme: number,
  estimated: number | null | undefined,
): Avancement {
  if (!estimated) return "sans-estime";
  const part = consomme / estimated;
  if (part > 1) return "depasse";
  if (part >= 0.8) return "proche";
  return "en-cours";
}
