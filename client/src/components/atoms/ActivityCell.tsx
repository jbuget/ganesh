import type { HTMLAttributes } from "react";

import type { ActivityLevel } from "@/lib/statistics";

/** Sky, as everywhere a mark says « this is live »; slate for a quiet day. */
const SHADES: Record<ActivityLevel, string> = {
  0: "bg-slate-100",
  1: "bg-sky-200",
  2: "bg-sky-300",
  3: "bg-sky-500",
  4: "bg-sky-700",
};

interface ActivityCellProps extends HTMLAttributes<HTMLSpanElement> {
  level: ActivityLevel;
}

/**
 * One day of the mosaic: a small square, darker the busier the day.
 *
 * The same square draws the legend, which is why it takes the pointer's
 * handlers and the accessible name from its caller rather than owning them.
 */
export function ActivityCell({ level, ...props }: ActivityCellProps) {
  return <span {...props} className={`size-3 rounded-[2px] ${SHADES[level]}`} />;
}
