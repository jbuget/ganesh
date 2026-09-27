import type { WorkNature } from "@/lib/api/generated/model";

/**
 * The trades a day is declared under, in the order they are offered.
 *
 * They name a hat rather than an act: here a developer also does the ops, a
 * designer does both UX and UI, and whoever steers carries the product,
 * the delivery and the coaching at once. Naming the act would leave a
 * developer's day on Terraform undecidable.
 */
export const WORK_NATURES: { value: WorkNature; label: string }[] = [
  { value: "development", label: "Développement" },
  { value: "design", label: "Design" },
  { value: "project_management", label: "Pilotage" },
];

const BY_VALUE = new Map(WORK_NATURES.map((nature) => [nature.value, nature.label]));

export function workNatureLabel(value: WorkNature | null | undefined): string | null {
  return value ? (BY_VALUE.get(value) ?? value) : null;
}
