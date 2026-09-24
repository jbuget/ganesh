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
   * The mission this row hangs under, shown only at the head of its group.
   *
   * Named once rather than beside every trade: a dozen rows repeating « API
   * Sitetracker » in grey read as noise, and the grid is already sorted so
   * that a mission's trades follow one another.
   */
  mission?: string | null;
  /** Whether the row names a trade, and so reads as set under its mission. */
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
      className="flex min-w-0 items-start"
      onMouseMove={(event) => follow(event, content)}
      onMouseLeave={leave}
    >
      <span className="flex min-w-0 flex-col">
        {mission && (
          <span className="truncate font-medium text-slate-900">{mission}</span>
        )}
        <span
          className={[
            "truncate",
            // Set in, so a trade reads as part of the mission above rather
            // than as a mission of its own.
            isUnderItsMission ? "pl-3 text-slate-600" : "",
          ].join(" ")}
        >
          {label}
        </span>
      </span>
      {tooltip}
    </span>
  );
}
