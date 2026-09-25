import { ReminderCadence } from "@/lib/api/generated/model";

/**
 * How often one is written to, said in French.
 *
 * The server names a cadence in the vocabulary of the domain — `WEEKLY` — and
 * never in the one the reader uses. Turning the one into the other is the
 * interface's business, and it happens here rather than in the component so
 * that every wording is under test.
 *
 * The letter itself is composed by the API, which has no browser in the loop:
 * its French lives on the server, and deliberately needs far less of it. See
 * `docs/notifications-email.md`.
 */
export interface ReminderChoice {
  value: ReminderCadence;
  /** What one picks, read first. */
  label: string;
  /** What picking it means, read under the label. */
  detail: string;
}

/**
 * The three cadences, from the most frequent to none at all.
 *
 * « Jamais » closes the list rather than opening it: one reads the way out
 * last, having seen what there is to turn down.
 */
export const REMINDER_CHOICES: readonly ReminderChoice[] = [
  {
    value: ReminderCadence.DAILY,
    label: "Chaque jour",
    detail: "Un e-mail les jours ouvrés, uniquement si quelque chose vous attend.",
  },
  {
    value: ReminderCadence.WEEKLY,
    label: "Chaque semaine",
    detail: "Un e-mail le premier jour ouvré de la semaine, s'il y a de quoi.",
  },
  {
    value: ReminderCadence.NEVER,
    label: "Jamais",
    detail: "Aucun e-mail. Les notifications restent lisibles dans Ganesh.",
  },
] as const;

export function reminderCadenceLabel(cadence: ReminderCadence): string {
  return REMINDER_CHOICES.find((choice) => choice.value === cadence)?.label ?? cadence;
}
