import type {
  AuditLogEntryResponse,
  ProjectCategory,
  ProjectPriority,
  ProjectStatus,
} from "@/lib/api/generated/model";
import { category, phaseLabel, priority } from "@/lib/board";
import { formatDecimalDays, formatSpelledDate } from "@/lib/dates";
import { departmentLabel } from "@/lib/departments";
import { CRITICALITIES, SERVICE_LINKS, SERVICE_TYPES } from "@/lib/service-sheet";

/**
 * One line of the log, said in French.
 *
 * The server writes what happened in the vocabulary of the domain — `entry.set`,
 * `scoping`, `landlords` — and never in the one the reader uses. Turning the
 * one into the other is the interface's business, and it happens here rather
 * than in the component so that every wording is under test: a log that says
 * « a modifié status » says nothing to whoever opens it.
 */
export interface AuditSentence {
  /** What was done, read straight after the name of who did it. */
  action: string;
  /** The before, when showing it says more than the action alone. */
  from?: string;
  /** The after, always alongside a `from`. */
  to?: string;
}

/** Nothing recorded on that side — an axis that was blank, a date not yet set. */
const NOTHING = "—";

/** Fields whose French name reads straight after « a modifié ». */
const FIELD_LABELS: Record<string, string> = {
  estimated_days: "la charge estimée",
  category: "l'axe stratégique",
  priority: "la priorité",
  go_live_date: "la date de mise en service",
  kind: "la nature de la mission",
  slug: "l'adresse publique",
  summary: "le résumé",
  description: "la fiche détaillée",
  criticality: "la criticité",
  service_type: "le type de service",
  hosting: "l'hébergement",
  has_microsoft_entra: "l'authentification Entra",
  team: "l'équipe",
  slack_channel: "le canal Slack",
  business_contacts: "les contacts métier",
  departments: "les pôles concernés",
  stack: "la stack technique",
  tags: "les étiquettes",
  depends_on: "les dépendances",
  monday_item_id: "le lien Monday",
  monday_subitem_id: "le lien Monday du lot",
  ...Object.fromEntries(
    SERVICE_LINKS.map(({ field, label }) => [field, `le lien ${label}`]),
  ),
};

/** What a French label expects on either side of the arrow. */
type Wording = (raw: string) => string;

const FROM_A_LIST =
  (one: Wording): Wording =>
  (raw) =>
    raw
      .split(",")
      .map((item) => one(item.trim()))
      .filter(Boolean)
      .join(", ");

const byValue =
  (table: readonly { value: string; label: string }[]): Wording =>
  (raw) =>
    table.find((row) => row.value === raw)?.label ?? raw;

/** How each field's stored value is read back. Anything else reads as it is. */
const VALUE_WORDINGS: Record<string, Wording> = {
  status: (raw) => phaseLabel(raw as ProjectStatus),
  category: (raw) => category(raw as ProjectCategory)?.label ?? raw,
  priority: (raw) => priority(raw as ProjectPriority)?.label ?? raw,
  estimated_days: (raw) => days(raw),
  criticality: byValue(CRITICALITIES),
  service_type: byValue(SERVICE_TYPES),
  departments: FROM_A_LIST((raw) => departmentLabel(raw as never)),
  go_live_date: (raw) => formatSpelledDate(raw),
};

/** A stored decimal read as the grid spells it: « 0,5 j », « 12 j ». */
function days(raw: string): string {
  const value = Number(raw);
  return Number.isNaN(value) ? raw : `${formatDecimalDays(value)} j`;
}

/** Python writes a boolean as « True » / « False ». */
function isTrue(raw: string | null): boolean {
  return raw === "True";
}

function wording(field: string | null, raw: string | null): string {
  if (raw === null) return NOTHING;
  const say = field === null ? undefined : VALUE_WORDINGS[field];
  return say ? say(raw) : raw;
}

/** The two ends of a change, left out entirely when neither was recorded. */
function movement(
  field: string | null,
  before: string | null,
  after: string | null,
): Pick<AuditSentence, "from" | "to"> {
  if (before === null && after === null) return {};
  return { from: wording(field, before), to: wording(field, after) };
}

/** « pour Nino Garo » — said only when it was not one's own month. */
function onBehalfOf(entry: AuditLogEntryResponse): string {
  const target = entry.target_user;
  if (!target || target.id === entry.actor?.id) return "";
  return ` pour ${target.display_name}`;
}

function onTheDay(entry: AuditLogEntryResponse): string {
  return entry.day ? ` le ${formatSpelledDate(entry.day)}` : "";
}

/** Gestures on a mission field that read as something other than « a modifié ». */
function fieldSentence(entry: AuditLogEntryResponse): AuditSentence {
  const { field, old_value: before, new_value: after } = entry;

  if (field === "label")
    return { action: "a renommé la mission", ...movement(field, before, after) };

  // A flag that carries a gesture is said as that gesture: « a archivé » is
  // what happened, « is_active : oui → non » is how it was stored.
  if (field === "is_active")
    return {
      action: isTrue(after) ? "a désarchivé la mission" : "a archivé la mission",
    };

  if (field === "is_published")
    return {
      action: isTrue(after)
        ? "a publié la fiche service"
        : "a retiré la fiche service du catalogue",
    };

  // The id of a project says nothing to a reader, and looking up its name would
  // mean a request per line: the gesture is named, the mission is not.
  if (field === "parent_id")
    return {
      action:
        after === null
          ? "a détaché la mission de son projet"
          : "a rattaché la mission à un projet",
    };

  return {
    action: `a modifié ${field === null ? "la mission" : (FIELD_LABELS[field] ?? field)}`,
    ...movement(field, before, after),
  };
}

const ROLES: Record<string, { joined: string; left: string }> = {
  contributor: { joined: "aux intervenants", left: "des intervenants" },
  lead: { joined: "comme référent", left: "de son rôle de référent" },
};

function role(raw: string | null, side: "joined" | "left"): string {
  return (ROLES[raw ?? ""] ?? ROLES.contributor)[side];
}

/** One line of the log, said in French. */
export function auditSentence(entry: AuditLogEntryResponse): AuditSentence {
  const { old_value: before, new_value: after } = entry;
  const who = entry.target_user?.display_name ?? "quelqu'un";

  switch (entry.action) {
    case "entry.set":
      // A correction and a first declaration are not the same fact: one says
      // how much was booked, the other says the figure moved.
      return before === null
        ? {
            action: `a déclaré ${days(after ?? "")}${onTheDay(entry)}${onBehalfOf(entry)}`,
          }
        : {
            action: `a modifié la déclaration du ${formatSpelledDate(entry.day ?? "")}${onBehalfOf(entry)}`,
            from: days(before),
            to: days(after ?? ""),
          };

    case "entry.clear":
      return {
        action: `a effacé ${days(before ?? "")}${onTheDay(entry)}${onBehalfOf(entry)}`,
      };

    case "project.create":
      return { action: "a créé la mission" };

    case "project.delete":
      return { action: "a supprimé la mission" };

    case "project.status_change":
      return { action: "a changé la phase", ...movement("status", before, after) };

    case "project.update":
      return fieldSentence(entry);

    case "project.assign":
      return { action: `a ajouté ${who} ${role(after, "joined")}` };

    case "project.unassign":
      return { action: `a retiré ${who} ${role(before, "left")}` };

    case "update.post":
      return { action: "a publié une mise à jour" };

    case "update.edit":
      return { action: "a modifié une mise à jour" };

    case "update.remove":
      return { action: "a supprimé une mise à jour" };

    default:
      // Nothing else carries a mission, so nothing else reaches this log. Said
      // rather than left blank: a line with no wording would read as a bug.
      return { action: "a effectué une action" };
  }
}

/** One day of the log, and the gestures made that day. */
export interface AuditDay {
  /** The day itself, in ISO form, so the caller decides how to spell it. */
  day: string;
  entries: AuditLogEntryResponse[];
}

/**
 * The log cut into days.
 *
 * A thousand lines in a row read as one block: the day is what one navigates
 * by, and it is said once rather than on every line. The order is the one the
 * server served — most recent first — and nothing is re-sorted here: a page
 * that reordered what it was given would no longer stack onto the next.
 */
export function groupAuditByDay(entries: AuditLogEntryResponse[]): AuditDay[] {
  const days: AuditDay[] = [];
  for (const entry of entries) {
    const day = entry.at.slice(0, 10);
    const current = days.at(-1);
    if (current?.day === day) current.entries.push(entry);
    else days.push({ day, entries: [entry] });
  }
  return days;
}
