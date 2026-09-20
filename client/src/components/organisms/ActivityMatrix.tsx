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
  /** What the movement column is measured against, named. */
  against: string;
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
  against,
  empty,
}: ActivityMatrixProps) {
  return (
    <section>
      <h2 className="mb-2 text-sm font-semibold text-slate-900">{title}</h2>
      {/* Three columns nobody can read on their own: the unit, the
          denominator and the point of comparison are all invisible from the
          headings alone. */}
      <p className="mb-3 text-sm text-slate-500">
        Jours déclarés sur la période. La part se lit sur tout le temps déclaré, hors
        projet compris — les lignes d&apos;un bloc ne font donc pas 100 %.
        L&apos;évolution compare {against}.
      </p>

      {lines.length === 0 ? (
        <p className="text-sm text-slate-500">{empty}</p>
      ) : (
        // The matrix scrolls on its own, on both axes, so that the coverage
        // note and the titles above it stay put while the columns move.
        //
        // Bounded in height on purpose: a container that scrolls sideways is
        // a scroll container on both axes whatever CSS one writes — `clip`
        // computes to `hidden` as soon as the other axis is `auto` — and one
        // with nothing to scroll vertically swallows the wheel and leaves the
        // page looking frozen. Given a height it can overflow, the wheel does
        // the obvious thing: it scrolls the table, then the page beneath it.
        //
        // The block that fits under the cap — off-project work, a handful of
        // lines — is untouched by it.
        <div className="max-h-[70vh] overflow-auto [&_[data-slot=table-container]]:overflow-visible">
          <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
            <TableHeader className={TABLE_HEADER}>
              <TableRow>
                <TableHead className="sticky left-0 z-20 bg-white">Projet</TableHead>
                <TableHead
                  className="text-right"
                  title="Jours déclarés sur la période, lots compris"
                >
                  Jours
                </TableHead>
                <TableHead
                  className="text-right"
                  title="Part de tout le temps déclaré sur la période, hors projet compris"
                >
                  Part du déclaré
                </TableHead>
                <TableHead
                  className={`text-right whitespace-nowrap ${STRONG_SEPARATOR}`}
                  title={`Jours gagnés ou perdus par rapport ${against}`}
                >
                  Évolution
                </TableHead>
                {contributors.map((someone) => (
                  <TableHead key={someone.id} className="text-center whitespace-nowrap">
                    {someone.display_name}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>

            <TableBody>
              {lines.map((line) => (
                <ActivityMatrixRow
                  key={line.project_id}
                  line={line}
                  contributors={contributors}
                  against={against}
                />
              ))}

              <TableRow className="bg-slate-50 font-medium">
                <TableCell className="sticky left-0 z-0 bg-white">Total</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatDays(totalDays)}
                </TableCell>
                <TableCell />
                <TableCell className={STRONG_SEPARATOR} />
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
              </TableRow>
            </TableBody>
          </Table>
        </div>
      )}
    </section>
  );
}
