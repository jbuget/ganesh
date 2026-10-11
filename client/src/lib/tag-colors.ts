import { TagColor } from "@/lib/api/generated/model";

/**
 * What each colour of the palette shows, and what it is called.
 *
 * The API names the ten colours and the interface paints them, as a phase is
 * named by the domain and coloured here. The order is the palette's, and the
 * one the API declares: a picker that reshuffled itself could not be learnt.
 * The name is always written beside the mark, so the colour is never the only
 * thing that tells two tags apart.
 *
 * The mark is a text colour, for an icon: a shape drawn as a rotated box
 * forms a stacking context, which paints in front of the pinned columns of the
 * reference list when it scrolls under them.
 *
 * Whole class names, never built from the colour: Tailwind reads the source,
 * and a class assembled at run time would be purged.
 */
export const TAG_COLORS: { value: TagColor; label: string; mark: string }[] = [
  { value: TagColor.red, label: "Rouge", mark: "text-red-500" },
  { value: TagColor.orange, label: "Orange", mark: "text-orange-500" },
  { value: TagColor.amber, label: "Ambre", mark: "text-amber-500" },
  { value: TagColor.lime, label: "Citron vert", mark: "text-lime-500" },
  { value: TagColor.green, label: "Vert", mark: "text-emerald-500" },
  { value: TagColor.teal, label: "Turquoise", mark: "text-teal-500" },
  { value: TagColor.sky, label: "Ciel", mark: "text-sky-500" },
  { value: TagColor.blue, label: "Bleu", mark: "text-blue-600" },
  { value: TagColor.violet, label: "Violet", mark: "text-violet-500" },
  { value: TagColor.pink, label: "Rose", mark: "text-pink-500" },
];

const BY_VALUE = new Map(TAG_COLORS.map((color) => [color.value, color]));

/** The mark class of a colour, grey for one the interface does not know yet. */
export function tagMark(color: TagColor): string {
  return BY_VALUE.get(color)?.mark ?? "text-slate-400";
}

/** A colour said in French. */
export function tagColorLabel(color: string): string {
  return BY_VALUE.get(color as TagColor)?.label ?? color;
}
