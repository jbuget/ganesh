import type { DayPresence } from "@/lib/api/generated/model";
import { sayDay } from "@/lib/presence";

/**
 * Where somebody is, as a mark.
 *
 * Shape before colour, as everywhere in Ganesh: a filled disc on site, a ring
 * in télétravail, a dotted outline for a day away. One hue for the two ways of
 * being present — it is the same information in two modes, and it is full
 * against hollow that tells them apart. Read the same by whoever cannot tell
 * the colours, and legible down to the size the team board draws it.
 */
export function PresenceMark({
  day,
  size = "sm",
  labelled = true,
}: {
  day: DayPresence;
  size?: "sm" | "md";
  /** False inside a cell that already names the day in its own label. */
  labelled?: boolean;
}) {
  const box = size === "md" ? "size-[18px]" : "size-[13px]";
  const shape =
    day === "ON_SITE"
      ? "bg-sky-600 border-sky-600"
      : day === "REMOTE"
        ? "border-sky-600"
        : "border-dotted border-slate-300";

  return (
    <span
      role={labelled ? "img" : undefined}
      aria-label={labelled ? sayDay(day) : undefined}
      aria-hidden={labelled ? undefined : true}
      title={labelled ? sayDay(day) : undefined}
      className={`inline-block shrink-0 rounded-full border-2 ${box} ${shape}`}
    />
  );
}
