import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { NO_SORT, comparateurDeTri, type MissionSort } from "@/lib/mission-sort";

/** Une mission et, s'il s'agit d'un projet, les lots qui en dependent. */
export interface ProjectNode {
  mission: ProjectListItemResponse;
  lots: ProjectListItemResponse[];
}

const HORS_PROJET = "off_project";

/**
 * Organise le referentiel en arborescence : chaque projet suivi de ses lots.
 *
 * Le tri s'applique a chaque niveau separement — les projets entre eux, les
 * lots au sein de leur projet : ranger la liste ne doit pas arracher un
 * sous-projet a son parent.
 *
 * Un lot dont le parent est absent de la liste — filtre, archive — remonte au
 * premier niveau plutot que de disparaitre : une mission invisible serait une
 * mission qu'on croit supprimee.
 */
export function buildProjectTree(
  missions: ProjectListItemResponse[],
  sorted: MissionSort = NO_SORT,
): ProjectNode[] {
  const ordre = comparateurDeTri(sorted);
  const projets = missions.filter((m) => m.project.kind === "project");
  const lots = missions.filter((m) => m.project.kind === "work_package");
  const idsPresents = new Set(projets.map((m) => m.project.id));

  const noeuds: ProjectNode[] = [...projets].sort(ordre).map((mission) => ({
    mission,
    lots: lots.filter((l) => l.project.parent_id === mission.project.id).sort(ordre),
  }));

  const orphelins = lots
    .filter(
      (l) => l.project.parent_id === null || !idsPresents.has(l.project.parent_id),
    )
    .sort(ordre)
    .map((lot) => ({ mission: lot, lots: [] }));

  return [...noeuds, ...orphelins];
}

/** Activites hors projet, listees a part : elles n'ont ni lot ni estime. */
export function offProjectActivities(
  missions: ProjectListItemResponse[],
): ProjectListItemResponse[] {
  return missions
    .filter((m) => m.project.kind === HORS_PROJET)
    .sort(comparateurDeTri(NO_SORT));
}
