import type { Role } from "@/lib/api/generated/model";

/**
 * Functional roles, from the door to the platform.
 *
 * Same order as the server's `Role`, and for the same reason: nobody hands
 * out a role above their own. `RANK` below reads that order rather than
 * repeating it.
 */
export const ROLES: { value: Role; label: string; description: string }[] = [
  {
    value: "GUEST",
    label: "Invité",
    description: "Lit l'application sans rien y saisir.",
  },
  {
    value: "TEAMMATE",
    label: "Collaborateur",
    description: "Saisit son mois et celui de ses collègues.",
  },
  {
    value: "MANAGER",
    label: "Manager",
    description: "Rouvre un mois validé et gère les collaborateurs.",
  },
  {
    value: "ADMIN",
    label: "Administrateur",
    description: "Administre la plateforme et nomme les managers.",
  },
];

const BY_VALUE = new Map(ROLES.map((role) => [role.value, role.label]));

/** Where each role stands on the ladder. */
const RANK = new Map(ROLES.map((role, position) => [role.value, position]));

export function roleLabel(value: Role): string {
  return BY_VALUE.get(value) ?? value;
}

function rank(role: Role): number {
  return RANK.get(role) ?? 0;
}

/** Whether this role stands at `floor` on the ladder, or above. */
export function holds(role: Role | undefined, floor: Role): boolean {
  return role !== undefined && rank(role) >= rank(floor);
}

/** A guest reads the application whole and writes nothing into it. */
export function canWrite(role: Role | undefined): boolean {
  return role !== undefined && role !== "GUEST";
}

/**
 * Which roles `actor` may hand out to `target`.
 *
 * The two bounds the server carries, read the same way so that the list never
 * offers a choice the API would refuse: nobody hands out a role above their
 * own, and nobody moves somebody who stands above them. Nobody changes their
 * own role either — the picker is what says so, by offering nothing.
 *
 * An empty list means the role shows and does not open.
 */
export function assignableRoles(
  actor: { id?: number; role?: Role } | undefined,
  target: { id?: number; role: Role },
): Role[] {
  if (actor?.role === undefined || !holds(actor.role, "MANAGER")) return [];
  if (actor.id !== undefined && actor.id === target.id) return [];
  if (rank(target.role) > rank(actor.role)) return [];
  return ROLES.filter((role) => rank(role.value) <= rank(actor.role!)).map(
    (role) => role.value,
  );
}
