import type {
  ApiKeyResponse,
  ApiKeyScope,
  ApiKeyState,
} from "@/lib/api/generated/model";

/**
 * What the team reads about a service account.
 *
 * A key is used by a machine and answered for by a named human, whose role it
 * never inherits. It opens nothing until a route asks for one of its scopes. Every scope listed here opens at least one
 * route — a box that promised what the API does not keep would make this table
 * say what a key opens, and say it wrong.
 *
 * The two « Tous » cover what a route opens to machines, never everything the
 * API knows: a resource deliberately kept shut — the moods, given in
 * confidence — stays shut, because no route asks for a scope on it.
 */

export const SCOPES: { value: ApiKeyScope; label: string; hint: string }[] = [
  {
    value: "all:read",
    label: "Tous (lecture)",
    hint: "Toutes les lectures ouvertes aux machines, y compris celles qui s'y ajouteront",
  },
  {
    value: "all:write",
    label: "Tous (écriture)",
    hint: "Toutes les écritures ouvertes aux machines, y compris celles qui s'y ajouteront",
  },
  {
    value: "catalog:read",
    label: "Catalogue (lecture)",
    hint: "Lire les services publiés, ce que fait waat.tools",
  },
  {
    value: "roadmap:read",
    label: "Feuille de route (lecture)",
    hint: "Lire ce qui a été livré et ce qui est annoncé",
  },
  {
    value: "stats:read",
    label: "Statistiques (lecture)",
    hint: "Lire les chiffres du tableau de bord",
  },
  {
    value: "projects:read",
    label: "Projets (lecture)",
    hint: "Lire le référentiel des projets, leur détail et ce qu'ils ont coûté",
  },
  {
    value: "projects:write",
    label: "Projets (écriture)",
    hint: "Créer, modifier, archiver et importer des projets",
  },
  {
    value: "updates:write",
    label: "Mises à jour (écriture)",
    hint: "Publier sur le fil d'un projet",
  },
  {
    value: "entries:read",
    label: "Temps (lecture)",
    hint: "Exporter les temps déclarés sur une période",
  },
  {
    value: "users:read",
    label: "Équipe (lecture)",
    hint: "Lire l'annuaire des coéquipiers",
  },
  {
    value: "audit:read",
    label: "Journal (lecture)",
    hint: "Lire le journal des actions",
  },
];

const SCOPE_LABELS = new Map(SCOPES.map((scope) => [scope.value, scope.label]));

export function scopeLabel(scope: ApiKeyScope): string {
  return SCOPE_LABELS.get(scope) ?? scope;
}

/**
 * Which broad scope already grants a precise one.
 *
 * The same rule the server applies in `ApiKey.grants`: each « Tous » covers
 * the scopes of its own verb, and no other. The two are independent — neither
 * locks the other — so a key that reads and writes everything carries both,
 * and each stays untickable back.
 *
 * The form ticks and locks what a broad scope carries, so its reach is seen
 * where it is decided rather than discovered later in a log.
 */
export function coveredBy(
  scope: ApiKeyScope,
  chosen: ApiKeyScope[],
): ApiKeyScope | null {
  if (scope === "all:read" || scope === "all:write") return null;
  const broad = scope.endsWith(":read") ? "all:read" : "all:write";
  return chosen.includes(broad) ? broad : null;
}

/**
 * What is worth sending: the covered ones are dropped.
 *
 * A key granted « Tous (lecture) » needs nothing else recorded — the server
 * derives the rest, and a stored list of redundant scopes would only make the
 * table harder to read.
 */
export function pruneCovered(scopes: ApiKeyScope[]): ApiKeyScope[] {
  return scopes.filter((scope) => coveredBy(scope, scopes) === null);
}

/**
 * How the badge reads.
 *
 * `state` is derived by the entity and typed by the API: the record is exhaustive
 * by construction, and a state added upstream breaks the build here rather than
 * falling through to a blank badge.
 */
export const STATES: Record<ApiKeyState, { label: string; dot: string }> = {
  active: { label: "Active", dot: "bg-emerald-500" },
  expired: { label: "Expirée", dot: "bg-amber-500" },
  revoked: { label: "Révoquée", dot: "bg-slate-300" },
};

export function isUsable(key: ApiKeyResponse): boolean {
  return key.state === "active";
}

/**
 * Usable keys first, then the rest, each lot newest first.
 *
 * What still opens a door is what one comes to read; a revoked key stays
 * visible because the audit refers to it, but it waits at the bottom.
 */
export function sortKeys(keys: ApiKeyResponse[]): ApiKeyResponse[] {
  return [...keys].sort((a, b) => {
    if (isUsable(a) !== isUsable(b)) return isUsable(a) ? -1 : 1;
    return b.created_at.localeCompare(a.created_at);
  });
}

/** The expiry the form offers: a year, which is a deliberate default. */
export function oneYearFromNow(today: Date = new Date()): string {
  const expiry = new Date(today);
  expiry.setFullYear(expiry.getFullYear() + 1);
  return expiry.toISOString().slice(0, 10);
}
