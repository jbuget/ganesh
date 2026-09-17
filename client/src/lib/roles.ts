import type { Role } from "@/lib/api/generated/model";

/** Roles fonctionnels, du moins dotant au plus dotant. */
export const ROLES: { valeur: Role; libelle: string; description: string }[] = [
  {
    valeur: "TEAMMATE",
    libelle: "Collaborateur",
    description: "Saisit son mois et celui de ses collègues.",
  },
  {
    valeur: "MANAGER",
    libelle: "Manager",
    description: "Rouvre un mois validé et gère les collaborateurs.",
  },
];

const PAR_VALEUR = new Map(ROLES.map((role) => [role.valeur, role.libelle]));

export function libelleRole(valeur: Role): string {
  return PAR_VALEUR.get(valeur) ?? valeur;
}
