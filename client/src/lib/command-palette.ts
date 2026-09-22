import { CircleUser, type LucideIcon } from "lucide-react";

import type {
  AuditAction,
  ProjectListItemResponse,
  ProjectStatus,
  TouchedProjectResponse,
  UserResponse,
} from "@/lib/api/generated/model";
import { SCREENS } from "@/lib/navigation";
import { normalise } from "@/lib/search-text";

export type DestinationGroup = "recent" | "screen" | "project" | "person";

/** What each group is called, above the results it holds. */
export const GROUP_LABEL: Record<DestinationGroup, string> = {
  recent: "Activité récente",
  screen: "Écrans",
  project: "Projets",
  person: "Personnes",
};

/** Somewhere one can go, and what is read of it on the way. */
export interface Destination {
  /** Unique across the groups: a project and a teammate may share an id. */
  key: string;
  label: string;
  href: string;
  group: DestinationGroup;
  /** The icon a screen or a teammate is marked with. */
  Icon?: LucideIcon;
  /** A project's phase, which is what its mark says. */
  status?: ProjectStatus | null;
  /**
   * Read under the label, and searched like it: « Archivé », « Sous-projet de
   * X », an email address. It tells apart two projects whose names are close,
   * and lets one find a colleague by whichever of the two one has to hand.
   */
  hint?: string;
  /**
   * When it last moved, for a destination the palette offers on that ground.
   * Held as it was recorded and spelled out when drawn, so that a palette open
   * for an hour does not go on saying « à l'instant ».
   */
  at?: string;
  /** What moved it, already in the words the reader reads. */
  gesture?: string;
}

/**
 * What a project says of itself besides its name.
 *
 * Both halves show when both are true: a work package that has been archived
 * is neither of the two alone.
 */
function projectHint(
  project: ProjectListItemResponse["project"],
  parents: Map<number, string>,
): string | undefined {
  const said: string[] = [];

  if (project.kind === "work_package") {
    const parent = project.parent_id ? parents.get(project.parent_id) : undefined;
    said.push(parent ? `Sous-projet de ${parent}` : "Sous-projet");
  }
  if (project.kind === "off_project") said.push("Hors-projet");
  if (!project.is_active) said.push("Archivé");

  return said.length > 0 ? said.join(" · ") : undefined;
}

/** How many of the projects that have just moved the empty palette shows. */
const RECENT = 5;

/**
 * How many the register is asked for, which is more than are shown.
 *
 * The log knows nothing of archiving, so it may well name projects the palette
 * then drops. Asking for exactly what is shown would leave the section short
 * of a line each time one of them had been put away.
 */
export const TOUCHED_ASKED_FOR = RECENT * 4;

/** A gesture of the register, in the words the screen says it in. */
const GESTURE: Partial<Record<AuditAction, string>> = {
  "project.create": "Créé",
  "project.update": "Modifié",
  "project.status_change": "Phase changée",
  "project.assign": "Intervenant ajouté",
  "project.unassign": "Intervenant retiré",
  "attachment.add": "Fichier ajouté",
  "attachment.rename": "Fichier renommé",
  "attachment.remove": "Fichier supprimé",
};

/**
 * What a gesture is called on the line that announces it.
 *
 * « Modifié » covers whatever the register grows next: a gesture the screen
 * has no word for still says that something happened, which is what the line
 * is there for. Masculine throughout — what it agrees with is « le projet ».
 */
export function gestureLabel(action: AuditAction): string {
  return GESTURE[action] ?? "Modifié";
}

/** The last thing that happened to a project, and when. */
interface Movement {
  at: string;
  gesture: string;
}

/**
 * When each project last moved, from the two registers that know.
 *
 * An update carries its own date with the reference list; every other gesture
 * is read back from the log, no project carrying the date it last changed.
 * The freshest of the two wins: they answer the same question, and the older
 * one would announce a project as quiet while it was being worked on.
 */
function lastMovements(
  missions: ProjectListItemResponse[],
  touched: TouchedProjectResponse[],
): Map<number, Movement> {
  const moved = new Map<number, Movement>();

  function remember(projectId: number, at: string, gesture: string) {
    const known = moved.get(projectId);
    if (!known || new Date(at) > new Date(known.at))
      moved.set(projectId, { at, gesture });
  }

  for (const mission of missions) {
    if (mission.latest_update) {
      remember(mission.project.id, mission.latest_update.published_at, "Mise à jour");
    }
  }
  for (const one of touched) {
    remember(one.project_id, one.at, gestureLabel(one.action));
  }

  return moved;
}

/**
 * The projects that have just moved.
 *
 * Read through the reference list rather than beside it: a project the list
 * can no longer name is one the palette has nowhere to lead, and announcing a
 * line that goes nowhere would be worse than leaving it out. Archived ones are
 * left out too — the question the section answers is what is moving, and they
 * are not.
 */
function recentlyMoved(
  missions: ProjectListItemResponse[],
  touched: TouchedProjectResponse[],
): Destination[] {
  const moved = lastMovements(missions, touched);

  return missions
    .flatMap((mission) => {
      const movement = moved.get(mission.project.id);
      return movement && mission.project.is_active ? [{ mission, movement }] : [];
    })
    .sort(
      (one, other) =>
        new Date(other.movement.at).getTime() - new Date(one.movement.at).getTime(),
    )
    .slice(0, RECENT)
    .map(({ mission, movement }) => ({
      key: `recent:${mission.project.id}`,
      label: mission.project.label,
      href: `/projects/${mission.project.id}`,
      group: "recent" as const,
      status: mission.project.status,
      at: movement.at,
      gesture: movement.gesture,
    }));
}

/**
 * Everywhere the palette can lead.
 *
 * Built once from what is already loaded, and searched in memory: the
 * reference list is some seventy missions and the team a dozen people, which
 * is nothing to filter through and everything to wait for a round trip on.
 */
export function destinations({
  missions,
  teammates,
  touched = [],
}: {
  missions: ProjectListItemResponse[];
  teammates: UserResponse[];
  touched?: TouchedProjectResponse[];
}): Destination[] {
  const parents = new Map(missions.map(({ project }) => [project.id, project.label]));

  return [
    ...recentlyMoved(missions, touched),
    ...SCREENS.map(({ href, label, Icon }) => ({
      key: `screen:${href}`,
      label,
      href,
      group: "screen" as const,
      Icon,
    })),
    ...missions.map(({ project }) => ({
      key: `project:${project.id}`,
      label: project.label,
      href: `/projects/${project.id}`,
      group: "project" as const,
      status: project.status,
      hint: projectHint(project, parents),
    })),
    ...teammates.map((teammate) => ({
      key: `person:${teammate.id}`,
      label: teammate.display_name,
      // The panel, not the list: one looks a colleague up to read their
      // record, and the list is what one came from.
      href: `/users?user=${teammate.id}`,
      group: "person" as const,
      Icon: CircleUser,
      hint: teammate.email,
    })),
  ];
}

/**
 * How well a destination answers what was typed, smallest first.
 *
 * A name opening on what was typed comes before a name whose second word does,
 * which comes before one merely carrying it somewhere inside. Last comes what
 * only its hint answers for: one searched a name, and got an email.
 */
const NO_MATCH = Number.POSITIVE_INFINITY;

function rank(destination: Destination, wanted: string): number {
  const label = normalise(destination.label);

  if (label.startsWith(wanted)) return 0;
  if (label.split(/[^\p{L}\p{N}]+/u).some((word) => word.startsWith(wanted))) return 1;
  if (label.includes(wanted)) return 2;
  if (destination.hint && normalise(destination.hint).includes(wanted)) return 3;

  return NO_MATCH;
}

/**
 * What the palette shows for what has been typed.
 *
 * Nothing typed shows what has just moved and then the screens, rather than a
 * hundred lines nobody has asked anything of yet: one opens the palette either
 * to go somewhere known, or to pick up what one left. Once something is typed
 * the whole reference list answers, and the projects just shown answer under
 * their own name — twice in one list would be reading double.
 */
export function matching(all: Destination[], query: string): Destination[] {
  const wanted = normalise(query.trim());
  if (!wanted) {
    return all.filter((one) => one.group === "recent" || one.group === "screen");
  }

  return all
    .filter((one) => one.group !== "recent")
    .map((destination) => ({ destination, rank: rank(destination, wanted) }))
    .filter((found) => found.rank !== NO_MATCH)
    .sort((one, other) => one.rank - other.rank)
    .map((found) => found.destination);
}

/** A run of results, under the heading of the group they belong to. */
export interface Section {
  group: DestinationGroup;
  label: string;
  items: Destination[];
}

/**
 * The results, gathered under their headings.
 *
 * A group appears where its best result did: the ranking decides what leads,
 * and gathering only saves the eye from reading the kind of each line. Reading
 * the sections one after the other therefore gives back the ranked order,
 * which is what the selection travels along.
 */
export function grouped(found: Destination[]): Section[] {
  const sections: Section[] = [];

  for (const destination of found) {
    const section = sections.find((one) => one.group === destination.group);
    if (section) section.items.push(destination);
    else
      sections.push({
        group: destination.group,
        label: GROUP_LABEL[destination.group],
        items: [destination],
      });
  }

  return sections;
}
