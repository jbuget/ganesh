"use client";

import { SurfaceRow } from "@/components/molecules/SurfaceRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { SurfaceUsageResponse } from "@/lib/api/generated/model";
import { UNSEEN_SCREENS, summariseIdle } from "@/lib/surfaces";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface SurfaceUsageTableProps {
  usage: SurfaceUsageResponse;
}

/**
 * What each function of the product saw: who used it, how much, since when.
 *
 * The dashboard measured the entry grid alone while eleven other things were
 * built beside it. This is the line-by-line answer to « what serves, and what
 * serves nobody any more ».
 *
 * The order is the domain's and is never sorted here: ranked by traffic, the
 * idle lines would sink to the bottom where nobody reads them, and two
 * windows would no longer be comparable at a glance.
 *
 * Same frame as the teammates and the mission reference list: a strong rule
 * around, a strong rule under the titles, and the column that names the
 * function closed off from those that describe it.
 */
export function SurfaceUsageTable({ usage }: SurfaceUsageTableProps) {
  return (
    <div className="flex flex-col gap-2">
      {/* The shadcn container opens a scrolling context that would hold the
          header inside the table. */}
      <div className="[&_[data-slot=table-container]]:overflow-visible">
        <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
          <TableHeader className={TABLE_HEADER}>
            <TableRow>
              <TableHead className={STRONG_SEPARATOR}>Ce qu&apos;on y fait</TableHead>
              <TableHead className="w-28 text-right">Personnes</TableHead>
              <TableHead className="w-24 text-right">Gestes</TableHead>
              {/* People rather than gestures: one tidy-up afternoon doubles
                  the gestures, while somebody who came or stopped coming is
                  adoption itself. */}
              <TableHead className="w-24 text-right">Écart</TableHead>
              <TableHead className="w-40 text-right">
                Dernier usage
                {/* The only column the window selector does not govern. */}
                <span className="block text-xs font-normal text-slate-500">
                  à ce jour
                </span>
              </TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {usage.activities.map((activity) => (
              <SurfaceRow key={activity.surface} activity={activity} />
            ))}
          </TableBody>
        </Table>
      </div>

      <p className="text-xs text-slate-500">
        {summariseIdle(usage.idle_count)} {UNSEEN_SCREENS}
      </p>
    </div>
  );
}
