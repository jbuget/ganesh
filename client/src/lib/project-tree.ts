import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { rangPhase } from "@/lib/board";

/** Une mission et, s'il s'agit d'un projet, les lots qui en dependent. */
export interface ProjectNode {
  mission: ProjectListItemResponse;
  lots: ProjectListItemResponse[];
}

const HORS_PROJET = "hors_projet";

/**
 * Ou en est la mission d'abord, son nom ensuite.
 *
 * Le referentiel se parcourt comme le kanban se lit, de gauche a droite : ce
 * qui demarre en haut, ce qui tourne en bas. A phase egale, l'alphabet, seul
 * ordre ou l'on retrouve une mission dont on connait le nom.
 */
function parPhasePuisLabel(a: ProjectListItemResponse, b: ProjectListItemResponse) {
  const ecart = rangPhase(a.project.statut) - rangPhase(b.project.statut);
  return ecart !== 0 ? ecart : a.project.label.localeCompare(b.project.label, "fr");
}

/**
 * Organise le referentiel en arborescence : chaque projet suivi de ses lots.
 *
 * Un lot dont le parent est absent de la liste — filtre, archive — remonte au
 * premier niveau plutot que de disparaitre : une mission invisible serait une
 * mission qu'on croit supprimee.
 */
export function buildProjectTree(missions: ProjectListItemResponse[]): ProjectNode[] {
  const projets = missions.filter((m) => m.project.kind === "projet");
  const lots = missions.filter((m) => m.project.kind === "lot");
  const idsPresents = new Set(projets.map((m) => m.project.id));

  const noeuds: ProjectNode[] = projets.sort(parPhasePuisLabel).map((mission) => ({
    mission,
    lots: lots
      .filter((l) => l.project.parent_id === mission.project.id)
      .sort(parPhasePuisLabel),
  }));

  const orphelins = lots
    .filter(
      (l) => l.project.parent_id === null || !idsPresents.has(l.project.parent_id),
    )
    .sort(parPhasePuisLabel)
    .map((lot) => ({ mission: lot, lots: [] }));

  return [...noeuds, ...orphelins];
}

/** Activites hors projet, listees a part : elles n'ont ni lot ni estime. */
export function offProjectActivities(
  missions: ProjectListItemResponse[],
): ProjectListItemResponse[] {
  return missions.filter((m) => m.project.kind === HORS_PROJET).sort(parPhasePuisLabel);
}
