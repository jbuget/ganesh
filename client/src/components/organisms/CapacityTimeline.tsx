"use client";

import { WeekColumnHeader } from "@/components/atoms/WeekColumnHeader";
import { PersonLoadRow } from "@/components/molecules/PersonLoadRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { PersonLoadResponse } from "@/lib/api/generated/model";
import { formatMonthOf } from "@/lib/dates";
import { opensMonth } from "@/lib/planning";
import {
  STRONG_SEPARATOR,
  TABLE_HEADER,
  TABLE_LINES,
  TABLE_SPREAD,
  TABLE_WINDOW,
} from "@/lib/table-frame";

interface CapacityTimelineProps {
  people: PersonLoadResponse[];
  weeks: string[];
}

/**
 * Everyone's diary across the horizon: the walls and the gaps.
 *
 * The other half of an arbitration. The mission timeline says what lands late;
 * this one says why — who is full, and from when someone frees up. What is
 * declared stays told apart from what the projection placed: the first is a
 * fact, the second a hypothesis.
 */
export function CapacityTimeline({ people, weeks }: CapacityTimelineProps) {
  if (people.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        Aucun intervenant actif à charger.
      </p>
    );
  }

  // The strong rule closes the window, not the table: wider and taller than the
  // room it has, the table would carry its right edge and its bottom off screen
  // and leave the reading cut raw.
  //
  // The window is named and focusable: the weeks hold no control to tab
  // through, so without it they could only ever be reached with a mouse.
  return (
    <div
      role="region"
      aria-label="Charge de l'équipe, semaine par semaine"
      tabIndex={0}
      className={`h-full ${TABLE_WINDOW}`}
    >
      <div className={TABLE_SPREAD}>
        <Table className={`border-separate border-spacing-0 ${TABLE_LINES}`}>
          {/* The band of titles sits above the pinned column, which crosses the
              horizontal scrolling: it has to be raised over it too. */}
          <TableHeader className={`${TABLE_HEADER} z-20`}>
            <TableRow>
              <TableHead className={`sticky left-0 z-30 w-64 ${STRONG_SEPARATOR}`}>
                Intervenant
              </TableHead>
              <TableHead className="w-28 text-right">Jours libres</TableHead>
              <TableHead className="w-52">Se libère</TableHead>
              {weeks.map((week, index) => (
                <TableHead key={week} className="w-14 px-1">
                  <WeekColumnHeader
                    week={week}
                    opensMonth={opensMonth(weeks, index)}
                    monthLabel={formatMonthOf(week)}
                  />
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>

          <TableBody>
            {people.map((person) => (
              <PersonLoadRow key={person.user.id} person={person} />
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
