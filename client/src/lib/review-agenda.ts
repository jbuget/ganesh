import type { FlaggedUpdateResponse } from "@/lib/api/generated/model";

/** A project's share of the agenda: its name, and what is waiting under it. */
export interface AgendaChapter {
  projectId: number;
  label: string;
  items: FlaggedUpdateResponse[];
}

/**
 * The agenda, project by project rather than as one flat chronology.
 *
 * Read flat, the same project comes up and is dropped three times over, and
 * the meeting opens its thread three times. Gathered under its name, a
 * project's share reads as one subject.
 *
 * The server decides the order — the longest wait first — and the grouping
 * keeps it: a project takes the rank of its oldest line, and its lines keep
 * the order they came in.
 */
export function groupByProject(
  flagged: readonly FlaggedUpdateResponse[],
): AgendaChapter[] {
  const chapters = new Map<number, AgendaChapter>();
  for (const one of flagged) {
    const chapter = chapters.get(one.project_id);
    if (chapter) chapter.items.push(one);
    else
      chapters.set(one.project_id, {
        projectId: one.project_id,
        label: one.project_label,
        items: [one],
      });
  }
  return [...chapters.values()];
}

/**
 * How many lines are waiting, across every project.
 *
 * Its own function rather than a reduce inside the screen: the component
 * carries the rendering alone, and a total is a reading of the data.
 */
export function countWaiting(chapters: readonly AgendaChapter[]): number {
  return chapters.reduce((total, one) => total + one.items.length, 0);
}
