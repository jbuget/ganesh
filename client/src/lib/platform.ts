import type { Door, ServiceResponse } from "@/lib/api/generated/model";

/** How a door reads, in the words the team uses for it. */
const DOORS: Record<Door, { label: string; detail: string }> = {
  ENTRA: {
    label: "Microsoft Entra ID",
    detail: "Chaque requête porte un jeton signé par Entra.",
  },
  LOCAL: {
    label: "Porte de secours",
    detail: "Entra est éteint : un seul compte entre, avec un mot de passe.",
  },
  OPEN: {
    label: "Aucune",
    detail: "L'authentification est coupée. À ne jamais laisser en production.",
  },
};

export function doorLabel(door: Door): string {
  return DOORS[door].label;
}

export function doorDetail(door: Door): string {
  return DOORS[door].detail;
}

/**
 * What each service is called, and what its absence costs.
 *
 * Said here rather than on the server: the API answers what is wired, the
 * interface says what that means for whoever reads it. « Non câblé » alone
 * would read as a fault on three services out of four, where two of them
 * work perfectly well without.
 */
const SERVICES: Record<string, { label: string; without: string }> = {
  entra: {
    label: "Microsoft Entra ID",
    without: "Personne ne se connecte par Entra.",
  },
  gemini: {
    label: "Modèle de La Gazette",
    without: "Les digests sortent sur leurs faits, sans chapeau.",
  },
  smtp: {
    label: "Serveur de mail",
    without: "Aucune lettre de rappel ne part.",
  },
  s3: {
    label: "Stockage des fichiers",
    without: "Les projets ne portent aucun fichier.",
  },
};

export function serviceLabel(name: string): string {
  return SERVICES[name]?.label ?? name;
}

/** What to read on a service's line: its address, or what it costs to lack it. */
export function serviceSays(service: ServiceResponse): string {
  if (service.configured) return service.detail;
  return SERVICES[service.name]?.without ?? "Non câblé.";
}
