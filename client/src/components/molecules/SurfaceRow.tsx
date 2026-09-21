"use client";

import { TableCell, TableRow } from "@/components/ui/table";
import type { SurfaceActivityResponse } from "@/lib/api/generated/model";
import {
  formatLastUse,
  formatPeopleDelta,
  isIdle,
  surfaceCounted,
  surfaceLabel,
} from "@/lib/surfaces";
import { STRONG_SEPARATOR } from "@/lib/table-frame";

interface SurfaceRowProps {
  activity: SurfaceActivityResponse;
}

/**
 * One function of the product, and what it saw.
 *
 * A function nobody used is marked on the figure alone — colour marks, it
 * does not fill — and the whole line is not tinted: eight idle lines in an
 * amber block would read as a broken screen rather than as a reading.
 */
export function SurfaceRow({ activity }: SurfaceRowProps) {
  const idle = isIdle(activity);
  const counted = surfaceCounted(activity.surface);

  return (
    // Same relief as the teammates and the reference list: the page tint on
    // the row, white on the cell that names it, one step behind on hover.
    <TableRow className="group bg-slate-50 hover:bg-slate-100">
      <TableCell
        className={`bg-white py-2 align-top group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
      >
        <span className="font-medium">{surfaceLabel(activity.surface)}</span>
        {counted && <p className="mt-0.5 text-xs text-slate-500">{counted}</p>}
      </TableCell>
      <TableCell className="py-2 text-right align-top tabular-nums">
        {activity.people}
      </TableCell>
      <TableCell
        className={`py-2 text-right align-top tabular-nums ${
          idle ? "font-medium text-amber-600" : ""
        }`}
      >
        {activity.gestures}
      </TableCell>
      <TableCell className="py-2 text-right align-top tabular-nums text-slate-500">
        {formatPeopleDelta(activity.delta_in_people)}
      </TableCell>
      <TableCell
        className={`py-2 text-right align-top ${
          activity.last_used_on ? "text-slate-500" : "text-amber-600"
        }`}
      >
        {formatLastUse(activity.last_used_on)}
      </TableCell>
    </TableRow>
  );
}
