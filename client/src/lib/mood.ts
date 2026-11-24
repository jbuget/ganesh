import { Frown, Laugh, Meh, Smile } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { MoodLevel } from "@/lib/api/generated/model";
import { formatWeekdayDate } from "@/lib/dates";
import { StarStruck } from "@/lib/star-struck";

/**
 * How a day felt, from the worst to the best.
 *
 * A scale climbs, here as on any axis: the picker offers the faces low to
 * high, a day's answers lay out the same way, and a stacked bar is read in
 * that order too. The same five faces must not read one way on one screen and
 * the other way on the next.
 *
 * A coloured mark and a label in ordinary text, as phases and urgencies have:
 * colour marks, it does not fill.
 *
 * The middle of the scale is a good day, and it smiles: a day that went well
 * is what most days are, and answering it with a flat mouth reads as if
 * something had gone wrong. Below it, a day that was mixed or hard; above it,
 * a very good one, then one that stood out.
 *
 * The scale reads by the face — a falling mouth, a flat one, a smile, a grin,
 * stars in the eyes — and not by shade alone, so that it stays readable for
 * whoever cannot tell the colours apart. A face is also what one answers
 * with: a mark out of five would turn a day into a grade, and one does not
 * grade a day.
 *
 * The hover shade is written out beside the colour rather than composed from
 * it: Tailwind reads the source for class names, and one built at run time
 * would never be generated.
 */
export const MOODS: {
  value: MoodLevel;
  label: string;
  icon: LucideIcon;
  colour: string;
  hover: string;
  /** The filled shade, for the one place a surface is legitimate: a chart. */
  fill: string;
}[] = [
  {
    value: "hard",
    label: "Difficile",
    icon: Frown,
    colour: "text-rose-500",
    hover: "hover:text-rose-500",
    fill: "bg-rose-500",
  },
  {
    value: "mixed",
    label: "Mitigée",
    icon: Meh,
    colour: "text-amber-500",
    hover: "hover:text-amber-500",
    fill: "bg-amber-500",
  },
  {
    value: "good",
    label: "Bonne",
    icon: Smile,
    colour: "text-sky-500",
    hover: "hover:text-sky-500",
    fill: "bg-sky-500",
  },
  {
    value: "great",
    label: "Très bonne",
    icon: Laugh,
    colour: "text-emerald-500",
    hover: "hover:text-emerald-500",
    fill: "bg-emerald-500",
  },
  {
    value: "exceptional",
    label: "Exceptionnelle",
    icon: StarStruck,
    colour: "text-violet-500",
    hover: "hover:text-violet-500",
    fill: "bg-violet-500",
  },
];

const MOODS_BY_VALUE = new Map(MOODS.map((level) => [level.value, level]));

export function mood(value: MoodLevel | null | undefined) {
  return value ? (MOODS_BY_VALUE.get(value) ?? null) : null;
}

/**
 * How a day one may still answer for is named.
 *
 * The other open day is named and dated rather than called « hier »: over a
 * weekend it is the Friday, and « hier » would name the Sunday nobody worked.
 */
export function dayLabel(day: string, today: string): string {
  return day === today ? "Aujourd'hui" : formatWeekdayDate(day);
}
