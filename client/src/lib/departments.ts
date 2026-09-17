import type { Department } from "@/lib/api/generated/model";

/** Departements de l'entreprise, dans l'ordre ou l'equipe les enonce. */
export const DEPARTEMENTS: { valeur: Department; libelle: string }[] = [
  { valeur: "administratif_financier", libelle: "Administratif & Financier" },
  { valeur: "bailleurs", libelle: "Bailleurs" },
  { valeur: "copropriete", libelle: "Copropriété" },
  { valeur: "service_client", libelle: "Service client" },
  { valeur: "operations", libelle: "Opérations" },
  { valeur: "systeme_information", libelle: "Système d'information" },
  { valeur: "ressources_humaines", libelle: "Ressources humaines" },
  { valeur: "marketing_communication_rse", libelle: "Marketing, Communication & RSE" },
  { valeur: "tertiaire", libelle: "Tertiaire" },
  { valeur: "autre", libelle: "Autre" },
];

const PAR_VALEUR = new Map(DEPARTEMENTS.map((d) => [d.valeur, d.libelle]));

export function libelleDepartement(valeur: Department): string {
  return PAR_VALEUR.get(valeur) ?? valeur;
}
