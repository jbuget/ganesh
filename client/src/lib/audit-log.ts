import type {
  AuditLogEntryResponse,
  ProjectCategory,
  ProjectPriority,
  ProjectStatus,
  Role,
} from "@/lib/api/generated/model";
import { category, phaseLabel, priority } from "@/lib/board";
import { formatDecimalDays, formatMonthOf, formatSpelledDate } from "@/lib/dates";
import { departmentLabel } from "@/lib/departments";
import { parisDay } from "@/lib/instants";
import { roleLabel } from "@/lib/roles";
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
/**
 * Which log the sentence is being read in.
 *
 * The same gesture is not said the same way on a mission's log and on a
 * month's: each screen already says one thing, and a sentence repeating it
 * pushes out what the reader actually came for. A mission's page says which
 * mission; a month's says whose month and which one.
 *
 * « all » is the register read across, where the screen says nothing: every
 * gesture has to name what it was about. It is also the only reading that
 * meets the gestures no mission carries — a role changed, a key minted, a
 * gazette generated — which is why they are said here at all.
 */
export interface AuditReading {
  read: "project" | "month" | "all";
}

const ON_A_MISSION: AuditReading = { read: "project" };

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

/**
 * A role said the way the team picks it, not the way the column stores it.
 *
 * `ROLES` in this module is the other kind of role — leading or contributing
 * to a mission. What the picker offers is read through its own helper, which
 * is also what the « Utilisateurs » screen says.
 */
function roleWording(raw: string | null): string {
  return raw === null ? NOTHING : roleLabel(raw as Role);
}

/** Fields whose French name reads straight after « a modifié ». */
const FIELD_LABELS: Record<string, string> = {
  estimated_days: "la charge estimée",
  category: "l'axe stratégique",
  priority: "la priorité",
  go_live_date: "la date de mise en service",
  kind: "la nature du projet",
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

/**
 * « pour Nino Garo » — said only when it was not one's own month.
 *
 * Read inside that very month, it is said by the screen and dropped here: the
 * line would otherwise name, on every row, the one person the page is about.
 */
function onBehalfOf(entry: AuditLogEntryResponse, reading: AuditReading): string {
  const target = entry.target_user;
  if (reading.read === "month") return "";
  if (!target || target.id === entry.actor?.id) return "";
  return ` pour ${target.display_name}`;
}

/** Whether the month worked on was the actor's own. */
function isOwnMonth(entry: AuditLogEntryResponse): boolean {
  return entry.target_user === null || entry.target_user.id === entry.actor?.id;
}

/** « son mois de septembre 2026 », « le mois de septembre 2026 ». */
function theMonth(entry: AuditLogEntryResponse): string {
  const month = entry.day ? formatMonthOf(entry.day) : "un mois";
  return isOwnMonth(entry) ? `son mois de ${month}` : `le mois de ${month}`;
}

/** « sur son mois de septembre 2026 », « sur le mois de septembre 2026 ». */
function ontoTheMonth(entry: AuditLogEntryResponse): string {
  return `sur ${theMonth(entry)}`;
}

/**
 * The same month, introduced by « de » — and contracted where French says so.
 *
 * « de le mois » is not a sentence: the two forms are written out rather than
 * glued together from a preposition and a noun phrase.
 */
function fromTheMonth(entry: AuditLogEntryResponse): string {
  const month = entry.day ? formatMonthOf(entry.day) : "un mois";
  return isOwnMonth(entry) ? `de son mois de ${month}` : `du mois de ${month}`;
}

function onTheDay(entry: AuditLogEntryResponse): string {
  return entry.day ? ` le ${formatSpelledDate(entry.day)}` : "";
}

/** Gestures on a mission field that read as something other than « a modifié ». */
function fieldSentence(entry: AuditLogEntryResponse): AuditSentence {
  const { field, old_value: before, new_value: after } = entry;

  if (field === "label")
    return { action: "a renommé le projet", ...movement(field, before, after) };

  // A flag that carries a gesture is said as that gesture: « a archivé » is
  // what happened, « is_active : oui → non » is how it was stored.
  if (field === "is_active")
    return {
      action: isTrue(after) ? "a désarchivé le projet" : "a archivé le projet",
    };

  if (field === "is_published")
    return {
      action: isTrue(after)
        ? "a publié la fiche service"
        : "a retiré la fiche service du catalogue",
    };

  // The id of a project says nothing to a reader, and looking up its name would
  // mean a request per line: the gesture is named, the mission is not.
  // A link is named rather than counted: « les liens » moving says nothing,
  // and the name is what the screen showed it under.
  if (field === "links")
    return {
      action:
        after === null
          ? `a retiré le lien « ${before} »`
          : `a ajouté le lien « ${after} »`,
    };

  if (field === "parent_id")
    return {
      action:
        after === null
          ? "a détaché le projet du sien"
          : "a rattaché le projet à un autre",
    };

  return {
    action: `a modifié ${field === null ? "le projet" : (FIELD_LABELS[field] ?? field)}`,
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
export function auditSentence(
  entry: AuditLogEntryResponse,
  reading: AuditReading = ON_A_MISSION,
): AuditSentence {
  const { old_value: before, new_value: after } = entry;
  const who = entry.target_user?.display_name ?? "quelqu'un";
  const withinTheMonth = reading.read === "month";

  switch (entry.action) {
    case "entry.set":
      // A correction and a first declaration are not the same fact: one says
      // how much was booked, the other says the figure moved.
      return before === null
        ? {
            action: `a déclaré ${days(after ?? "")}${onTheDay(entry)}${onBehalfOf(entry, reading)}`,
          }
        : {
            action: `a modifié la déclaration du ${formatSpelledDate(entry.day ?? "")}${onBehalfOf(entry, reading)}`,
            from: days(before),
            to: days(after ?? ""),
          };

    case "entry.clear":
      return {
        action: `a effacé ${days(before ?? "")}${onTheDay(entry)}${onBehalfOf(entry, reading)}`,
      };

    // Read inside the month it is about, the month is not named again — and
    // the mission is not named either: it is the one thing the month's log
    // carries beside the sentence, where a mission's log carries the month.
    case "month.project_add":
      return withinTheMonth
        ? { action: "a ajouté le projet" }
        : {
            action: `a mis le projet ${ontoTheMonth(entry)}${onBehalfOf(entry, reading)}`,
          };

    case "month.project_remove":
      return withinTheMonth
        ? { action: "a retiré le projet" }
        : {
            action: `a retiré le projet ${fromTheMonth(entry)}${onBehalfOf(entry, reading)}`,
          };

    // What locks a month and what gives it back: the two gestures a month's
    // log exists to show, and which no mission ever carries.
    case "month.validate":
      return {
        action: withinTheMonth ? "a validé le mois" : `a validé ${theMonth(entry)}`,
      };

    case "month.reopen":
      return {
        action: withinTheMonth ? "a rouvert le mois" : `a rouvert ${theMonth(entry)}`,
      };

    case "simulation.create":
      return { action: `a enregistré la simulation « ${after ?? ""} »` };

    case "simulation.update":
      return { action: `a modifié la simulation « ${after ?? ""} »` };

    case "simulation.delete":
      return { action: `a supprimé la simulation « ${after ?? ""} »` };

    case "user.create":
      return { action: "a rejoint Ganesh" };

    // What a mission never carries, and a month neither: these reach a log
    // only where the whole register is read.
    case "user.role_change":
      return {
        action: `a changé le rôle de ${who}`,
        from: roleWording(before),
        to: roleWording(after),
      };

    case "user.deactivate":
      return { action: `a désactivé le compte de ${who}` };

    case "user.activate":
      return { action: `a réactivé le compte de ${who}` };

    // Which fields moved is in the payload, which no screen reads: what the
    // line says is whose sheet was touched, and when.
    case "user.identity_update":
      return { action: `a modifié la fiche de ${who}` };

    // Which days, and from where, is in the payload and read on the team's
    // presence board. The line says that the week moved, never why it did:
    // that is nobody's to record.
    case "user.presence_declare":
      return { action: "a déclaré sa semaine" };

    // Which cadence is in the payload and read on one's own profile. The line
    // says that somebody chose, never what a letter then said: a channel
    // leaves no trace, only the gesture that opened or closed it.
    case "user.reminder_choose":
      return { action: "a choisi sa fréquence de rappel" };

    // A manager sending the round by hand — the morning the clock got it
    // wrong, or a first letter before trusting the whole thing to a schedule.
    // How many letters went out is in the payload, which no screen reads: the
    // manager was told on the spot, and the line says the campaign was run.
    case "reminder.run":
      return { action: "a lancé les rappels par e-mail" };

    // A key is named by its masked public part — the only piece of it the
    // register holds, the secret having never been written anywhere.
    case "api_key.create":
      return { action: `a créé la clé d'API ${after ?? ""}`.trimEnd() };

    case "api_key.revoke":
      return { action: `a révoqué la clé d'API ${before ?? ""}`.trimEnd() };

    case "api_key.update":
      return {
        action: "a modifié une clé d'API",
        from: before ?? NOTHING,
        to: after ?? NOTHING,
      };

    case "gazette.generate":
      return {
        action: `a généré La Gazette de ${entry.day ? formatMonthOf(entry.day) : "un mois"}`,
      };

    case "project.create":
      return { action: "a créé le projet" };

    // The only gesture whose mission the line cannot name: `project_id` is
    // null the moment the row goes. What it was called travels on the line,
    // and nowhere else — so it is said here rather than left to the row.
    case "project.delete":
      return {
        action: `a supprimé le projet${before ? ` « ${before} »` : ""}`,
      };

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

    // The file is named rather than counted: « a ajouté un fichier » on a
    // project that carries a dozen says nothing one came to the Journal for.
    // The name travels on the line — by now the file may be gone.
    case "attachment.add":
      return { action: `a ajouté le fichier « ${after} »` };

    case "attachment.remove":
      return { action: `a supprimé le fichier « ${before} »` };

    // Both names, and the log's own two columns carry them: what it was
    // called is as much the fact as what it is called now.
    case "attachment.rename":
      return {
        action: "a renommé un fichier",
        from: before ?? NOTHING,
        to: after ?? NOTHING,
      };

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
    const day = parisDay(entry.at);
    const current = days.at(-1);
    if (current?.day === day) current.entries.push(entry);
    else days.push({ day, entries: [entry] });
  }
  return days;
}
