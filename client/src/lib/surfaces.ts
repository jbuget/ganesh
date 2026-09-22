/**
 * The functions of the product, said in French.
 *
 * The API names a function in the domain's vocabulary — `phase_progress`,
 * `machine_access` — and the reader gets it here, as the audit log already
 * works. Under test, because a table nobody can read is not one.
 *
 * **A line is named after the gesture, never after the screen.** Moving a
 * card on the Kanban and changing the same field on the project sheet write
 * the very same thing, and declaring a day comes as readily from the grid as
 * from a terminal: a line called « Kanban » would read zero on a month where
 * every card moved from a form.
 */
import type { Surface } from "@/lib/api/generated/model";
import { formatSpelledDate } from "@/lib/dates";

interface SurfaceWording {
  /** What one does there, as somebody would say it. */
  label: string;
  /**
   * What the figures count, wherever the plain reading would be wrong.
   *
   * Left out where the label says it all: a precision under every line would
   * be read by nobody, and the three that matter would go down with it.
   */
  counted?: string;
}

const WORDINGS: Record<Surface, SurfaceWording> = {
  time_entry: { label: "Saisie des temps" },
  month_closing: { label: "Clôture des mois", counted: "validations et réouvertures" },
  project_registry: { label: "Référentiel de projets" },
  phase_progress: {
    label: "Avancement des phases",
    counted: "depuis le Kanban ou depuis la fiche",
  },
  assignment: { label: "Affectation des contributeurs" },
  project_updates: { label: "Actualités de projet" },
  project_files: {
    label: "Fichiers de projet",
    counted: "dépôts, renommages, suppressions",
  },
  planning: { label: "Planification", counted: "simulations enregistrées" },
  gazette: { label: "La Gazette", counted: "numéros générés" },
  mood: {
    label: "Moral",
    counted: "humeurs déposées ; ce qu'elles disent n'est pas lu ici",
  },
  notifications: { label: "Notifications", counted: "notifications ouvertes" },
  work_rhythm: { label: "Rythme de travail", counted: "rythmes déclarés" },
  team_admin: { label: "Gestion de l'équipe" },
  api_keys: { label: "Clés API", counted: "créations, modifications, révocations" },
  machine_access: {
    label: "Accès machine",
    counted: "clés ayant servi ; seul leur dernier appel est connu",
  },
};

export function surfaceLabel(surface: Surface): string {
  return WORDINGS[surface]?.label ?? surface;
}

export function surfaceCounted(surface: Surface): string | undefined {
  return WORDINGS[surface]?.counted;
}

/**
 * The screens the table cannot see, named rather than left out in silence.
 *
 * They only ever read, and nothing records that they were opened. Giving
 * them a line at zero would state a fact the register never held.
 */
export const UNSEEN_SCREENS =
  "L'Accueil, la Feuille de route, la Synthèse d'activité et cette page ne font " +
  "que lire : rien n'enregistre qu'on les a ouvertes, elles n'ont donc pas de ligne.";

/**
 * Movement in people: « +2 », « −1 », « = ».
 *
 * An equals sign rather than an em dash: the count held, which is a reading.
 * The dash says « there is nothing to read », and that would be false.
 */
export function formatPeopleDelta(delta: number): string {
  if (delta === 0) return "=";
  // A true minus sign, not a hyphen: at this size the hyphen reads as a dash.
  return delta > 0 ? `+${delta}` : `−${Math.abs(delta)}`;
}

/**
 * When a function was last used: « 17 sept. 2026 », or « jamais ».
 *
 * « Jamais » rather than an em dash: nobody having ever opened it is a fact,
 * where the dash would say the figure is missing.
 */
export function formatLastUse(day: string | null | undefined): string {
  return day ? formatSpelledDate(day) : "jamais";
}

/** How many functions served nobody, said in French. */
export function summariseIdle(count: number): string {
  if (count === 0) return "Toutes les fonctions ont servi sur la période.";
  return count > 1
    ? `${count} fonctions n'ont servi à personne sur la période.`
    : "1 fonction n'a servi à personne sur la période.";
}
