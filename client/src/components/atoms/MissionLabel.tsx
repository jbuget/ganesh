"use client";

import { formatDecimalDays } from "@/lib/dates";
import { useCursorTooltip } from "@/lib/use-tooltip-curseur";

interface MissionLabelProps {
  label: string;
  consommeJ: number;
  estimeJ: number | null;
}

/**
 * A mission's label, with its progress in a tooltip.
 *
 * The name may be truncated: the tooltip gives it back in full, along with what
 * is consumed against the estimate. One tooltip carries both, so as not to
 * compete with the browser's native one.
 */
export function MissionLabel({ label, consommeJ, estimeJ }: MissionLabelProps) {
  const { tooltip, follow, leave } = useCursorTooltip();

  const content = (
    <>
      <span className="font-medium">{label}</span>
      {estimeJ !== null && (
        <span className="ml-2 text-slate-300">
          {formatDecimalDays(consommeJ)}/{estimeJ} jrs. estimés
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
      <span className="truncate">{label}</span>
      {tooltip}
    </span>
  );
}
