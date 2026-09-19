import type {
  Criticality,
  ProjectResponse,
  ServiceType,
} from "@/lib/api/generated/model";

/**
 * What the service catalogue reads on a mission.
 *
 * The vocabulary is shared with waat.tools, which publishes these sheets: the
 * labels here are the ones a reader will find over there.
 */

export const CRITICALITIES: { value: Criticality; label: string }[] = [
  { value: "critical", label: "Critique" },
  { value: "standard", label: "Standard" },
  { value: "secondary", label: "Secondaire" },
];

export const SERVICE_TYPES: { value: ServiceType; label: string }[] = [
  { value: "frontend", label: "Webapp" },
  { value: "backend", label: "Backend" },
  { value: "api", label: "API" },
  { value: "fullstack", label: "Fullstack" },
  { value: "worker", label: "Worker" },
  { value: "tool", label: "Script" },
];

/** The named addresses of a service, in the order the catalogue reads them. */
export const SERVICE_LINKS = [
  { field: "production_link", label: "Production" },
  { field: "staging_link", label: "Staging" },
  { field: "repository_link", label: "Code" },
  { field: "documentation_link", label: "Documentation" },
  { field: "monitoring_link", label: "Monitoring" },
  { field: "project_management_link", label: "Gestion de projet" },
  { field: "stats_page_link", label: "Page stats" },
  { field: "stats_api_link", label: "Données stats" },
] as const;

export type ServiceLinkField = (typeof SERVICE_LINKS)[number]["field"];

/** Everything the service sheet can change on the mission itself, in one call. */
export type SheetFields = Partial<Record<ServiceLinkField, string | null>> & {
  slug?: string | null;
  is_published?: boolean;
  summary?: string | null;
  criticality?: Criticality | null;
  service_type?: ServiceType | null;
  hosting?: string | null;
  has_microsoft_entra?: boolean;
  team?: string | null;
  slack_channel?: string | null;
};

/**
 * What still stands between a mission and its public page.
 *
 * The button that publishes says why it cannot, rather than letting the server
 * refuse: one reads the reason where one acts.
 */
export function publicationBlockers(project: ProjectResponse): string[] {
  const missing: string[] = [];
  if (project.kind === "off_project") {
    missing.push("une activité hors projet ne se publie pas");
    return missing;
  }
  if (!project.slug) missing.push("l'adresse publique");
  if (!project.summary) missing.push("le résumé");
  if (!project.criticality) missing.push("la criticité");
  if (!project.service_type) missing.push("le type");
  return missing;
}

/**
 * An enumeration as one says it: « a, b et c ».
 *
 * Four items strung together by « et » read like a stutter; the comma does the
 * work and the last « et » closes the sentence.
 */
export function frenchList(items: string[]): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} et ${items[items.length - 1]}`;
}

/** Turns a label into the address it would take in the catalogue. */
export function suggestSlug(label: string): string {
  return label
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 100)
    .replace(/-+$/g, "");
}
