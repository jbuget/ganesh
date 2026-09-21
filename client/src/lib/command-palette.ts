import { CircleUser, type LucideIcon } from "lucide-react";

import type {
  ProjectListItemResponse,
  ProjectStatus,
  UserResponse,
} from "@/lib/api/generated/model";
import { SCREENS } from "@/lib/navigation";
import { normalise } from "@/lib/search-text";

export type DestinationGroup = "screen" | "project" | "person";

/** What each group is called, above the results it holds. */
export const GROUP_LABEL: Record<DestinationGroup, string> = {
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
}: {
  missions: ProjectListItemResponse[];
  teammates: UserResponse[];
}): Destination[] {
  const parents = new Map(missions.map(({ project }) => [project.id, project.label]));

  return [
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
 * Nothing typed shows the screens alone: the palette opens on where one can
 * go, rather than on a hundred lines nobody has asked anything of yet.
 */
export function matching(all: Destination[], query: string): Destination[] {
  const wanted = normalise(query.trim());
  if (!wanted) return all.filter((one) => one.group === "screen");

  return all
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
