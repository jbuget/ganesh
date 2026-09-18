"use client";

import { MessageCircle } from "lucide-react";
import type { ReactNode } from "react";

import { useCursorTooltip } from "@/lib/use-tooltip-curseur";

interface UpdatesCounterProps {
  count: number;
  /**
   * What the tooltip shows on hover — the latest message, formatted.
   *
   * It comes from the parent and not from here: rendering markdown is another
   * component, and an atom composes none. Absent, the count shows without a
   * tooltip.
   */
  apercu?: ReactNode;
  /** Leads to the thread itself: the preview makes one want to reply. */
  onOpen: () => void;
}

/**
 * A mission's follow-up thread, as one number.
 *
 * Knowing there are three messages does not say whether they need reading: the
 * tooltip gives the latest in full, which most often saves opening the panel.
 * When it does not, the click leads to the thread itself.
 *
 * A mission with no update shows nothing: in a table, only what can be read is
 * displayed.
 */
export function UpdatesCounter({ count, apercu, onOpen }: UpdatesCounterProps) {
  const { tooltip, follow, leave } = useCursorTooltip({ rich: true });

  if (count === 0) return null;

  return (
    <button
      type="button"
      aria-label={`${count} ${count > 1 ? "mises à jour" : "mise à jour"}`}
      // The whole row already opens the mission: without stopping propagation,
      // the click would open it twice, the second time on the wrong tab.
      onClick={(event) => {
        event.stopPropagation();
        onOpen();
      }}
      onMouseMove={(event) => apercu && follow(event, apercu)}
      onMouseLeave={leave}
      className="inline-flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 text-xs tabular-nums text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
    >
      {count}
      <MessageCircle className="size-3.5 shrink-0" aria-hidden />
      {tooltip}
    </button>
  );
}
