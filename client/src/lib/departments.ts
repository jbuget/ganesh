import type { Department } from "@/lib/api/generated/model";

/** Departements de l'entreprise, dans l'ordre ou l'equipe les enonce. */
export const DEPARTEMENTS: { value: Department; label: string }[] = [
  { value: "finance_admin", label: "Administratif & Financier" },
  { value: "landlords", label: "Bailleurs" },
  { value: "condominium", label: "Copropriété" },
  { value: "customer_service", label: "Service client" },
  { value: "operations", label: "Opérations" },
  { value: "information_systems", label: "Système d'information" },
  { value: "human_resources", label: "Ressources humaines" },
  { value: "marketing_communication_csr", label: "Marketing, Communication & RSE" },
  { value: "commercial_real_estate", label: "Tertiaire" },
  { value: "other", label: "Autre" },
];

const PAR_VALEUR = new Map(DEPARTEMENTS.map((d) => [d.value, d.label]));

export function libelleDepartement(value: Department): string {
  return PAR_VALEUR.get(value) ?? value;
}
