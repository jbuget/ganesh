import type { OrgLevel } from "@/lib/api/generated/model";

/**
 * Where somebody sits in the company, from the top down.
 *
 * It says nothing about what they may do here — that is the role's business,
 * and the two are read side by side on the sheet without ever agreeing.
 */
export const ORG_LEVELS: { value: OrgLevel; label: string }[] = [
  { value: "comex", label: "COMEX" },
  { value: "comop", label: "COMOP" },
  { value: "collaborator", label: "Collaborateur" },
];

const BY_VALUE = new Map(ORG_LEVELS.map((level) => [level.value, level.label]));

/** Where each level stands, read off the order above rather than written down. */
const RANK = new Map(ORG_LEVELS.map((level, position) => [level.value, position]));

/**
 * How far up the company a level sits, as a number.
 *
 * For the one thing a label cannot do: put a list of people in order. The
 * alphabet would file « COMEX » between « Collaborateur » and « COMOP », which
 * says nothing anybody is looking for.
 */
export function orgLevelRank(value: OrgLevel): number {
  return RANK.get(value) ?? ORG_LEVELS.length;
}

export function orgLevelLabel(value: OrgLevel): string {
  return BY_VALUE.get(value) ?? value;
}
