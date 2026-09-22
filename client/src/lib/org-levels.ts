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

export function orgLevelLabel(value: OrgLevel): string {
  return BY_VALUE.get(value) ?? value;
}
