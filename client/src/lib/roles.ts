import type { Role } from "@/lib/api/generated/model";

/**
 * Functional roles, from the least to the most empowered.
 *
 * **The order is the ladder**, exactly as the domain declares it: `RANK` reads
 * nothing else. What lives here decides what a screen *offers*; the API is
 * what decides what is allowed, and refuses out loud either way.
 */
export const ROLES: { value: Role; label: string; description: string }[] = [
  {
    value: "GUEST",
    label: "Invité",
    description:
      "De l'entreprise, pas de l'équipe : dépose une demande, et rien d'autre.",
  },
  {
    value: "TEAMMATE",
    label: "Collaborateur",
    description: "Saisit son mois et celui de ses collègues.",
  },
  {
    value: "MANAGER",
    label: "Manager",
    description: "Rouvre un mois validé, arbitre les demandes et gère les comptes.",
  },
  {
    value: "ADMIN",
    label: "Administrateur",
    description:
      "Tout ce qu'un manager fait, et seul à pouvoir nommer un administrateur.",
  },
];

const BY_VALUE = new Map(ROLES.map((role) => [role.value, role.label]));
const RANK = new Map(ROLES.map((role, rank) => [role.value, rank]));

export function roleLabel(value: Role): string {
  return BY_VALUE.get(value) ?? value;
}

/** Whether `role` stands at least as high as `other` on the ladder. */
export function reaches(role: Role, other: Role): boolean {
  return (RANK.get(role) ?? 0) >= (RANK.get(other) ?? 0);
}

/**
 * Whether this account steers the team: a manager, or an admin above.
 *
 * Read wherever a screen used to test « MANAGER » on the nose. An admin turned
 * away there would be weaker than the rung below them.
 */
export function isManager<T extends { role: Role }>(
  user: T | null | undefined,
): user is T {
  return user != null && reaches(user.role, "MANAGER");
}

/** The ranks this account may hand out. Nobody confers above their own. */
export function grantableBy(actor: { role: Role } | null | undefined): Role[] {
  if (!isManager(actor)) return [];
  return ROLES.filter((role) => reaches(actor.role, role.value)).map(
    (role) => role.value,
  );
}

/**
 * Whether `actor` may act on `target`'s account — its rank, its access.
 *
 * The domain's two rules, mirrored so a screen does not offer what the API
 * would refuse: nobody touches their own account — a demotion or a
 * deactivation no route undoes — and nobody acts on somebody standing above
 * them. What rank may then be handed out is `grantableBy`'s answer.
 */
export function mayActOn(
  actor: { id: number; role: Role } | null | undefined,
  target: { id: number; role: Role },
): boolean {
  if (!actor || actor.id === target.id) return false;
  return isManager(actor) && reaches(actor.role, target.role);
}
