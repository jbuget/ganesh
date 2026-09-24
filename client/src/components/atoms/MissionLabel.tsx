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
  mission?: string | null;
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
      className="flex items-center"
      onMouseMove={(event) => follow(event, content)}
      onMouseLeave={leave}
    >
      {mission && (
        <span className="mr-1 shrink-0 truncate text-xs text-muted-foreground">
          {mission} ·
        </span>
      )}
      <span className="truncate">{label}</span>
      {tooltip}
    </span>
  );
}
