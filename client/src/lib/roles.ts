import type { Role } from "@/lib/api/generated/model";

/** Roles fonctionnels, du moins dotant au plus dotant. */
export const ROLES: { value: Role; label: string; description: string }[] = [
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
];

const PAR_VALEUR = new Map(ROLES.map((role) => [role.value, role.label]));

export function libelleRole(value: Role): string {
  return PAR_VALEUR.get(value) ?? value;
}
