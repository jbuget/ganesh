"use client";

import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { useCursorTooltip } from "@/lib/use-cursor-tooltip";

interface CardCounterProps {
  icon: LucideIcon;
  count: number;
  /** What the icon counts, singular then plural. */
  label: [string, string];
  /** What the screen reader announces when there is nothing to count. */
  empty: string;
  /**
   * What the tooltip shows on hover — the latest message, formatted.
   *
   * It comes from the parent and not from here: rendering markdown is another
   * component, and an atom composes none. Absent, the count shows without a
   * tooltip.
   */
  preview?: ReactNode;
}

/**
 * A count in a card's footer: an icon, and a number when there is one.
 *
 * The icon stays put at zero, with no number beside it: the card keeps the same
 * shape from one mission to the next, and absence then reads as fast as a
 * total. That is Monday's choice, whose cards serve as our reference.
 *
 * When the count announces a thread, the tooltip gives its latest message, as
 * in the reference list: knowing there are three messages does not say whether
 * they need reading.
 */
export function CardCounter({
  icon: Icone,
  count,
  label,
  empty,
  preview,
}: CardCounterProps) {
  const [singular, plural] = label;
  const { tooltip, follow, leave } = useCursorTooltip({ rich: true });

  return (
    <span
      aria-label={count === 0 ? empty : `${count} ${count > 1 ? plural : singular}`}
      onMouseMove={(event) => preview && follow(event, preview)}
      onMouseLeave={leave}
      className={`flex items-center gap-1 text-xs tabular-nums ${
        count === 0 ? "text-slate-300" : "text-slate-500"
      }`}
    >
      {count > 0 && count}
      <Icone className="size-3.5 shrink-0" aria-hidden />
      {tooltip}
    </span>
  );
}
