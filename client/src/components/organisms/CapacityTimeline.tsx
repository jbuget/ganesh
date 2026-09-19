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

interface CapacityTimelineProps {
  people: PersonLoadResponse[];
  weeks: string[];
}

function opensMonth(weeks: string[], index: number): boolean {
  if (index === 0) return true;
  return weeks[index].slice(0, 7) !== weeks[index - 1].slice(0, 7);
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

  return (
    <div className="w-max pr-6 [&_[data-slot=table-container]]:overflow-visible">
      <Table>
        <TableHeader className="sticky top-0 z-20 [&_th]:border-b [&_th]:border-b-slate-500 [&_th]:bg-slate-50">
          <TableRow>
            <TableHead className="sticky left-0 z-30 w-64 bg-slate-50">
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
  );
}
