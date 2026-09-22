/**
 * How a search reads what it is looking through.
 *
 * Written once and read by every screen that searches: a search answering
 * differently on two screens is two searches, and the reader has no way of
 * knowing which one they are using.
 */

/** Lowercase and unaccented: searching « copropriete » finds « copropriété ». */
export function normalise(body: string): string {
  return body
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}
