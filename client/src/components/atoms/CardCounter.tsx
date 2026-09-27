"use client";

import type { LucideIcon } from "lucide-react";
import type { MouseEvent, ReactNode } from "react";

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
  /**
   * Leads to what the count counts — a thread, for instance.
   *
   * Absent, the count shows without being clickable: not everything a card
   * counts has a screen of its own, and the card already opens the mission.
   */
  onOpen?: () => void;
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
 * they need reading. And when it leads somewhere, it leads there at zero as
 * well: one clicks the bubble of a mission nobody has written on precisely to
 * be the first.
 */
export function CardCounter({
  icon: Icon,
  count,
  label,
  empty,
  preview,
  onOpen,
}: CardCounterProps) {
  const [singular, plural] = label;
  const { tooltip, follow, leave } = useCursorTooltip({ rich: true });

  const what = count === 0 ? empty : `${count} ${count > 1 ? plural : singular}`;
  // The same geometry whether it leads anywhere or not: a card must not
  // change shape because one of its counts happens to be clickable.
  const look = [
    "flex items-center gap-1 rounded px-1 py-0.5 text-xs tabular-nums",
    count === 0 ? "text-slate-300" : "text-slate-500",
  ].join(" ");
  // The same bubble whether the count leads anywhere or not: what it shows
  // does not depend on what clicking it would do.
  const hover = {
    onMouseMove: (event: MouseEvent) => {
      if (preview) follow(event, preview);
    },
    onMouseLeave: leave,
  };
  const marking = (
    <>
      {count > 0 && count}
      <Icon className="size-3.5 shrink-0" aria-hidden />
      {tooltip}
    </>
  );

  if (!onOpen) {
    return (
      <span aria-label={what} {...hover} className={look}>
        {marking}
      </span>
    );
  }

  return (
    <button
      type="button"
      aria-label={what}
      // The whole card already opens the mission: without stopping
      // propagation, the click would open it twice, the second time on the
      // wrong tab.
      onClick={(event) => {
        event.stopPropagation();
        onOpen();
      }}
      {...hover}
      className={`${look} cursor-pointer transition-colors hover:bg-slate-100 hover:text-slate-700`}
    >
      {marking}
    </button>
  );
}
