"use client";

import { ActivityMatrixRow } from "@/components/molecules/ActivityMatrixRow";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type {
  ActivityLineResponse,
  ContributorResponse,
} from "@/lib/api/generated/model";
import { formatDays } from "@/lib/activity";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface ActivityMatrixProps {
  title: string;
  lines: ActivityLineResponse[];
  contributors: ContributorResponse[];
  /** Days the whole block weighs, drawn on its closing row. */
  totalDays: number;
  empty: string;
}

/**
 * Missions down the side, people across the top, days in the cells.
 *
 * The reading a manager opens to ask where the time went. Missions and what
 * happens around them are drawn in two blocks of their own: leave folded in
 * with the projects would leave no readable denominator for « 32 % sur
 * WAATcher ».
 */
export function ActivityMatrix({
  title,
  lines,
  contributors,
  totalDays,
  empty,
}: ActivityMatrixProps) {
  return (
    <section>
      <h2 className="mb-2 text-sm font-semibold text-slate-900">{title}</h2>

      {lines.length === 0 ? (
        <p className="text-sm text-slate-500">{empty}</p>
      ) : (
        <div className="[&_[data-slot=table-container]]:overflow-visible">
          <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
            <TableHeader className={TABLE_HEADER}>
              <TableRow>
                <TableHead className={STRONG_SEPARATOR}>Projet</TableHead>
                {contributors.map((someone) => (
                  <TableHead key={someone.id} className="text-center">
                    {someone.display_name}
                  </TableHead>
                ))}
                <TableHead className="text-right">Total</TableHead>
                <TableHead className="text-right">Part</TableHead>
                <TableHead className="text-right">Évolution</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {lines.map((line) => (
                <ActivityMatrixRow
                  key={line.project_id}
                  line={line}
                  contributors={contributors}
                />
              ))}

              <TableRow className="bg-slate-50 font-medium">
                <TableCell className={`bg-white ${STRONG_SEPARATOR}`}>Total</TableCell>
                {contributors.map((someone) => (
                  <TableCell
                    key={someone.id}
                    className="text-center tabular-nums text-slate-700"
                  >
                    {formatDays(
                      lines.reduce(
                        (days, line) =>
                          days + (line.days_by_contributor[someone.id] ?? 0),
                        0,
                      ),
                    )}
                  </TableCell>
                ))}
                <TableCell className="text-right tabular-nums">
                  {formatDays(totalDays)}
                </TableCell>
                <TableCell />
                <TableCell />
              </TableRow>
            </TableBody>
          </Table>
        </div>
      )}
    </section>
  );
}
