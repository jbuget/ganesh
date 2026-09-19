import type { ApiKeyResponse, ApiKeyScope } from "@/lib/api/generated/model";

/**
 * What the team reads about a service account.
 *
 * A key belongs to a machine, never to a person, and it opens nothing until a
 * route asks for one of its scopes.
 */

export const SCOPES: { value: ApiKeyScope; label: string; hint: string }[] = [
  {
    value: "catalog:read",
    label: "Catalogue",
    hint: "Lire les services publiés, ce que fait waat.tools",
  },
  { value: "projects:read", label: "Missions", hint: "Lire le référentiel" },
  {
    value: "projects:write",
    label: "Missions (écriture)",
    hint: "Créer et modifier des missions",
  },
  { value: "entries:read", label: "Temps", hint: "Lire les temps déclarés" },
];

const SCOPE_LABELS = new Map(SCOPES.map((scope) => [scope.value, scope.label]));

export function scopeLabel(scope: ApiKeyScope): string {
  return SCOPE_LABELS.get(scope) ?? scope;
}

/** How the badge reads. `state` comes from the server: one truth, not two. */
export const STATES: Record<string, { label: string; dot: string }> = {
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
