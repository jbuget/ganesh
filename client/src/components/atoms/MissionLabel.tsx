"use client";

import { formatDecimalDays } from "@/lib/dates";
import { useCursorTooltip } from "@/lib/use-cursor-tooltip";

interface MissionLabelProps {
  label: string;
  /**
   * The mission the row hangs under, when the label names an activity.
   *
   * Shown small beside the name, because two missions both cut into
   * « Développement » would otherwise read as the same line — and it is the
   * mission one recognises a row by.
   */
  /**
   * The mission this row hangs under, named on every row that carries a trade.
   *
   * Each row stands on its own: two missions both cut into « Développement »
   * would otherwise give two lines reading alike, and one scans this column
   * looking for a mission rather than for a trade.
   */
  mission?: string | null;
  /** Whether the row names a trade, and so reads under its mission. */
  isUnderItsMission?: boolean;
  consumedDays: number;
  estimatedDays: number | null;
}

/**
 * A mission's label, with its progress in a tooltip.
 *
 * The name may be truncated: the tooltip gives it back in full, along with what
 * is consumed against the estimate. One tooltip carries both, so as not to
 * compete with the browser's native one.
 */
export function MissionLabel({
  label,
  mission = null,
  isUnderItsMission = false,
  consumedDays,
  estimatedDays,
}: MissionLabelProps) {
  const { tooltip, follow, leave } = useCursorTooltip();

  const content = (
    <>
      {mission && <span className="text-slate-300">{mission} · </span>}
      <span className="font-medium">{label}</span>
      {estimatedDays !== null && (
        <span className="ml-2 text-slate-300">
          {formatDecimalDays(consumedDays)}/{estimatedDays} jrs. estimés
        </span>
      )}
    </>
  );

  return (
    <span
      className="flex min-w-0 items-center"
      onMouseMove={(event) => follow(event, content)}
      onMouseLeave={leave}
    >
      {mission && isUnderItsMission && (
        <>
          {/* Plain text rather than a faint grey: the mission is what one
              scans this column for, and washing it out made it read as an
              aside on the row it actually names. */}
          {/* The mission gives way first: names run to fifty characters
              here, and a row whose trade is cut off is a row one cannot tell
              from its neighbour. The tooltip gives both back in full. */}
          <span className="min-w-0 truncate text-slate-900">{mission}</span>
          <span className="mx-1 shrink-0 text-slate-400" aria-hidden>
            ·
          </span>
        </>
      )}
      <span
        className={[
          "font-medium text-slate-900",
          // Never given up: the trade is what tells two rows of one mission
          // apart, and what the reader is choosing between.
          isUnderItsMission ? "shrink-0" : "truncate",
        ].join(" ")}
      >
        {label}
      </span>
      {tooltip}
    </span>
  );
}
