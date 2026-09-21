/**
 * The files a project carries, as a screen reads them.
 *
 * The address of a file is a relative path on purpose: it goes through the
 * BFF like everything else, so an `<img>` in an update and an `<a>` in the
 * Fichiers tab both travel with the session and never see the API directly.
 * It is also a *stable* address — it is written into the markdown of an
 * update, and something that expires could not be.
 */
import { formatParisMoment } from "@/lib/instants";

/** Where a file is shown from. The same address the markdown of a thread cites. */
export function contentUrl(projectId: number, attachmentId: number): string {
  return `/api/v1/projects/${projectId}/attachments/${attachmentId}/content`;
}

/** Where a file is saved from: the same address, asked to be offered. */
export function downloadUrl(projectId: number, attachmentId: number): string {
  return `${contentUrl(projectId, attachmentId)}?download=true`;
}

const UNITS = ["o", "ko", "Mo"];

/**
 * A size, as one says it: « 512 ko », « 1,4 Mo ».
 *
 * Kilobytes of 1024, and a decimal only where it says something: « 1,4 Mo »
 * is worth reading, « 1,0 Mo » is noise, and so is « 512,3 ko ».
 */
export function formatBytes(bytes: number): string {
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const rounded = unit === 0 || value >= 10 ? Math.round(value) : Math.round(value * 10) / 10;
  return `${String(rounded).replace(".", ",")} ${UNITS[unit]}`;
}

/** Who dropped a file, and when: « Téléversé par Alice Chen le 20/05/2026 à 13h35 ». */
export function uploadedBy(name: string, uploadedAt: string): string {
  return `Téléversé par ${name} le ${formatParisMoment(uploadedAt)}`;
}

/**
 * What a thread would lose if the file went.
 *
 * Nothing at all when no update shows it — the dialog then asks the plain
 * question, without a warning nobody needs.
 */
export function shownInUpdates(count: number): string | null {
  if (count <= 0) return null;
  return count === 1
    ? "Ce fichier est affiché dans une mise à jour, qui montrera une image manquante."
    : `Ce fichier est affiché dans ${count} mises à jour, qui montreront une image manquante.`;
}
