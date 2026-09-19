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
  if (!project.slug) missing.push("le slug");
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

/**
 * Where a published sheet is read, up to the identifier that names it.
 *
 * Shown in front of the field: an identifier asked for on its own reads as an
 * address to paste, and a whole URL lands in it.
 */
export const CATALOG_ADDRESS = "waat.tools/services/";

/** What the catalogue accepts as a slug: the domain rule, reflected here. */
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const SLUG_MAX_LENGTH = 100;

/**
 * Why a slug would be refused, said before the server has to say it.
 *
 * The API holds the rule and refuses the write; this is only its reflection,
 * so that what one reads is in French and names the shape expected. What one
 * is tempted to paste is a whole URL: the message answers that first.
 */
export function slugError(value: string | null): string | null {
  if (value === null || value === "") return null;
  if (value.length > SLUG_MAX_LENGTH) {
    return `Un slug ne dépasse pas ${SLUG_MAX_LENGTH} caractères.`;
  }
  if (!SLUG.test(value)) {
    return "Un slug s'écrit en minuscules, chiffres et tirets — « portail-bailleurs », pas une URL entière.";
  }
  return null;
}
