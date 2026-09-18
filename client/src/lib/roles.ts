import type { Role } from "@/lib/api/generated/model";

/** Functional roles, from the least to the most empowered. */
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

const BY_VALUE = new Map(ROLES.map((role) => [role.value, role.label]));

export function roleLabel(value: Role): string {
  return BY_VALUE.get(value) ?? value;
}
