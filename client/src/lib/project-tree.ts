import type { ProjectResponse } from "@/lib/api/generated/model";

/** Une mission et, s'il s'agit d'un projet, les lots qui en dependent. */
export interface ProjectNode {
  project: ProjectResponse;
  lots: ProjectResponse[];
}

const HORS_PROJET = "hors_projet";

function parLabel(a: ProjectResponse, b: ProjectResponse) {
  return a.label.localeCompare(b.label, "fr");
}

/**
 * Organise le referentiel en arborescence : chaque projet suivi de ses lots.
 *
 * Un lot dont le parent est absent de la liste — filtre, archive — remonte au
 * premier niveau plutot que de disparaitre : une mission invisible serait une
 * mission qu'on croit supprimee.
 */
export function buildProjectTree(projects: ProjectResponse[]): ProjectNode[] {
  const projets = projects.filter((p) => p.kind === "projet");
  const lots = projects.filter((p) => p.kind === "lot");
  const idsPresents = new Set(projets.map((p) => p.id));

  const noeuds: ProjectNode[] = projets.sort(parLabel).map((project) => ({
    project,
    lots: lots.filter((lot) => lot.parent_id === project.id).sort(parLabel),
  }));

  const orphelins = lots
    .filter((lot) => lot.parent_id === null || !idsPresents.has(lot.parent_id))
    .sort(parLabel)
    .map((lot) => ({ project: lot, lots: [] }));

  return [...noeuds, ...orphelins];
}

/** Activites hors projet, listees a part : elles n'ont ni lot ni estime. */
export function offProjectActivities(projects: ProjectResponse[]): ProjectResponse[] {
  return projects.filter((p) => p.kind === HORS_PROJET).sort(parLabel);
}
