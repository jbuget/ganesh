import type {
  NotificationResponse,
  ProjectStatus,
  Role,
} from "@/lib/api/generated/model";
import { phaseLabel } from "@/lib/board";
import { formatMonthOf } from "@/lib/dates";
import { roleLabel } from "@/lib/roles";

/**
 * One line of the inbox, said in French.
 *
 * The server says what happened in the vocabulary of the domain —
 * `project.assigned`, `referent`, `development` — and never in the one the
 * reader uses. Turning the one into the other is the interface's business, and
 * it happens here rather than in the component so that every wording is under
 * test: a notification one cannot read is not one.
 *
 * The user reads « projet », never « mission ».
 */
export interface NotificationSentence {
  /** Who acted, read first. */
  who: string;
  /** What they did, read straight after the name. */
  what: string;
  /** What it was done to: a project, a month, a key. */
  about?: string;
  /** What the line adds once the same gesture folded into it several times. */
  detail?: string;
  /** Where the line leads, when there is still something to open. */
  href?: string;
}

/** An account that has been removed still signs what it did. */
const GONE = "Un compte supprimé";

/** A project that no longer exists, and whose name nothing carries. */
const NAMELESS = "un projet";

/** How an assignment role reads. */
const ROLES: Record<string, string> = {
  lead: "référent",
  contributor: "intervenant",
};

function text(payload: NotificationResponse["payload"], key: string): string | null {
  const value = payload?.[key];
  return typeof value === "string" ? value : null;
}

/** The project's name, or the one kept beside it for when it is gone. */
function projectLabel(line: NotificationResponse): string {
  return line.project?.label ?? text(line.payload, "project_label") ?? NAMELESS;
}

function role(line: NotificationResponse): string {
  const raw = text(line.payload, "role") ?? "contributor";
  return ROLES[raw] ?? raw;
}

/** « janvier 2026 » — what a timesheet notification is about. */
function month(line: NotificationResponse): string {
  return line.day ? formatMonthOf(line.day) : "un mois";
}

/**
 * What each kind says, and what it says it about.
 *
 * Kept as one table rather than spread over the components: adding a kind
 * server-side and forgetting its French is then a missing line here, which the
 * test catches, and not a blank in the middle of somebody's inbox.
 */
const WORDINGS: Record<
  string,
  (line: NotificationResponse) => Pick<NotificationSentence, "what" | "about">
> = {
  "project.assigned": (line) => ({
    what: `vous a ajouté comme ${role(line)} sur`,
    about: projectLabel(line),
  }),
  "project.unassigned": (line) => ({
    what: `vous a retiré comme ${role(line)} de`,
    about: projectLabel(line),
  }),
  "timesheet.edited": (line) => ({
    what: "a modifié votre feuille de temps de",
    about: month(line),
  }),
  "month.reopened": (line) => ({
    what: "a rouvert votre feuille de temps de",
    about: month(line),
  }),
  "project.update_posted": (line) => ({
    what: "a publié une mise à jour sur",
    about: projectLabel(line),
  }),
  "project.status_changed": (line) => {
    const to = text(line.payload, "to");
    return {
      what: to
        ? `a fait passer en ${phaseLabel(to as ProjectStatus)}`
        : "a changé la phase de",
      about: projectLabel(line),
    };
  },
  "project.archived": (line) => ({
    what: "a archivé le projet",
    about: projectLabel(line),
  }),
  "project.deleted": (line) => ({
    what: "a supprimé le projet",
    about: projectLabel(line),
  }),
  "user.role_changed": (line) => {
    const to = text(line.payload, "to");
    return {
      what: "vous a donné le rôle",
      about: to ? roleLabel(to as Role) : undefined,
    };
  },
  "user.deactivated": () => ({ what: "a désactivé votre compte" }),
  "user.activated": () => ({ what: "a réactivé votre compte" }),
  "api_key.created": (line) => ({
    what: "a créé une clé API à votre nom",
    about: text(line.payload, "key_label") ?? undefined,
  }),
  "api_key.revoked": (line) => ({
    what: "a révoqué une clé API à votre nom",
    about: text(line.payload, "key_label") ?? undefined,
  }),
  "update.mention": (line) => ({
    what: "vous a mentionné dans une mise à jour sur",
    about: projectLabel(line),
  }),
  // The title travels on the line: what is waiting is read from the bell,
  // without having to open it — and it still reads if the need is withdrawn.
  "request.submitted": (line) => ({
    what: "a déposé la demande",
    about: text(line.payload, "title") ?? "une demande",
  }),
};

/** « 22 modifications » — said only once a gesture folded more than once. */
function repeats(line: NotificationResponse): string | undefined {
  if (line.count <= 1) return undefined;
  return `${line.count} modifications`;
}

/**
 * Where a line leads.
 *
 * A month notification opens the month it speaks of, a project one opens the
 * project. A line whose subject has been deleted leads nowhere — there is
 * nothing left to open, and a link to a 404 is worse than none.
 */
function destination(line: NotificationResponse): string | undefined {
  if (line.kind.startsWith("month.") || line.kind === "timesheet.edited") {
    return line.day ? `/timesheet?month=${line.day.slice(0, 7)}` : "/timesheet";
  }
  if (line.kind === "user.role_changed") return undefined;
  if (line.kind.startsWith("api_key.")) return "/api-mcp";
  if (line.kind.startsWith("request.")) {
    return line.request_id ? `/requests?request=${line.request_id}` : "/requests";
  }
  return line.project ? `/projects/${line.project.id}` : undefined;
}

/** One line of the inbox, ready to read. */
export function notificationSentence(line: NotificationResponse): NotificationSentence {
  const say = WORDINGS[line.kind];
  return {
    who: line.actor?.display_name ?? GONE,
    ...(say ? say(line) : { what: "a fait quelque chose qui vous concerne" }),
    detail: repeats(line),
    href: destination(line),
  };
}
