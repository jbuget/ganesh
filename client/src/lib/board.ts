import { Signal, SignalHigh, SignalLow, SignalMedium } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  ProjectCategory,
  ProjectPriority,
  ProjectStatus,
} from "@/lib/api/generated/model";

/**
 * Board phases, in column order.
 *
 * The dot follows progress, from the grey of what has not started to the green
 * of what is running: the colour places a column before one even reads its
 * title.
 */
export const PHASES: { status: ProjectStatus; label: string; dot: string }[] = [
  { status: "exploration", label: "Exploration", dot: "bg-slate-400" },
  { status: "scoping", label: "Cadrage", dot: "bg-violet-500" },
  { status: "development", label: "Réalisation", dot: "bg-blue-500" },
  { status: "validation", label: "Validation", dot: "bg-amber-500" },
  { status: "deployment", label: "Déploiement", dot: "bg-orange-500" },
  { status: "operations", label: "Exploitation", dot: "bg-emerald-500" },
];

const PHASES_PAR_STATUT = new Map(PHASES.map((p) => [p.status, p]));

/** Colour of a phase's dot. */
export function phaseDot(status: ProjectStatus): string {
  return PHASES_PAR_STATUT.get(status)?.dot ?? "bg-slate-300";
}

const RANGS_PHASES = new Map(PHASES.map((phase, rang) => [phase.status, rang]));

/**
 * Rank of a phase in the life cycle.
 *
 * Gives lists the same order as the kanban columns: a mission turns up in the
 * same relative place, whatever the screen. What carries no phase brings up
 * the rear rather than leading the way.
 */
export function phaseRank(status: ProjectStatus | null | undefined): number {
  return status ? (RANGS_PHASES.get(status) ?? PHASES.length) : PHASES.length;
}

const LIBELLES_PHASES = new Map(PHASES.map((p) => [p.status, p.label]));

export function phaseLabel(status: ProjectStatus): string {
  return LIBELLES_PHASES.get(status) ?? status;
}

/**
 * Strategic axes, with the shade that tells them apart.
 *
 * The same grammar as phases and urgencies: a coloured mark, an ordinary
 * label. The mark is square where a phase's is round: two marks of the same
 * shape on one line would blur together.
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
 * Urgencies, from the strongest to the weakest.
 *
 * A coloured mark and a label in ordinary text, as phases have: colour marks,
 * it does not fill. Three tinted surfaces per row — one for the phase, one for
 * the urgency, one for the axis — made the two least structuring columns shout
 * louder than the mission name.
 *
 * The scale reads by how full the gauge is — four bars, then three, two, one —
 * and not by shade alone: it stays readable for whoever cannot tell the colours
 * apart, or does not have them.
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
  // A low priority has no business drawing the eye: grey makes it recede, and
  // the eye keeps only what calls for a decision.
  { value: "low", label: "Basse", icon: SignalLow, colour: "text-slate-400" },
];

const PRIORITES_PAR_VALEUR = new Map(PRIORITIES.map((p) => [p.value, p]));

export function priority(value: ProjectPriority | null | undefined) {
  return value ? (PRIORITES_PAR_VALEUR.get(value) ?? null) : null;
}

/** How far along a mission is against its estimate. */
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
