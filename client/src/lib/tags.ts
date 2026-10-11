import { ApiError } from "@/lib/api/fetcher";
import type { TagUsageResponse } from "@/lib/api/generated/model";
import { normalise } from "@/lib/search-text";

/**
 * How many tags a project carries at most.
 *
 * The server holds the bound and refuses past it; this copy only lets the
 * picker say so before somebody types a ninth.
 */
export const MAX_TAGS_PER_PROJECT = 8;

/** A name as the server reads it: no case, no accents, one kind of separator. */
function keyOf(name: string): string {
  return normalise(name).replace(/[-_]/g, " ").split(/\s+/).filter(Boolean).join(" ");
}

/**
 * Whether two names are the same tag.
 *
 * The server decides — « Suez-Env », « suez env » and « Suez_Env » are one tag
 * there — and this reads it the same way, only so that a screen does not offer
 * to open a tag that exists.
 */
export function tagNamesAlike(a: string, b: string): boolean {
  return keyOf(a) === keyOf(b);
}

/**
 * Whether the picker offers to open a tag from what was typed.
 *
 * Only when nothing found already says it: a tag that merely contains the word
 * is no reason not to open the shorter one.
 */
export function proposesCreating(typed: string, found: TagUsageResponse[]): boolean {
  if (keyOf(typed) === "") return false;
  return !found.some((tag) => tagNamesAlike(tag.name, typed));
}

/**
 * What went wrong with a tag, said in French.
 *
 * The API says it in the vocabulary of the domain, and an interface says it in
 * the reader's: the status tells the two refusals worth explaining apart.
 */
export function tagFailureSaid(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 409) return "Un tag porte déjà ce nom : fusionnez-les plutôt.";
    if (error.status === 422 && /\btags at most\b/.test(error.detail)) {
      return `Un projet porte ${MAX_TAGS_PER_PROJECT} tags au plus.`;
    }
  }
  return "Ce tag n'a pas pu être enregistré.";
}

/**
 * The tags a row or a card has room for, and the ones it only counts.
 *
 * Nine tags on one line would stop being read: the first ones are drawn, the
 * rest are a number the reader can open the sheet for. Absent on a shape that
 * predates tags, which reads as carrying none.
 */
export function visibleTags<T>(
  tags: T[] | undefined,
  most: number,
): { shown: T[]; hidden: T[] } {
  const all = tags ?? [];
  return { shown: all.slice(0, most), hidden: all.slice(most) };
}
