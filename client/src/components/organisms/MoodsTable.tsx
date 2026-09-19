"use client";

import { MoodDayRow } from "@/components/molecules/MoodDayRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DayMoodsResponse } from "@/lib/api/generated/model";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface MoodsTableProps {
  /** The days of the window, the most recent first. */
  days: DayMoodsResponse[];
  headcount: number;
  today: string;
}

/**
 * The fortnight as a table: one line per day, the answers laid out on it.
 *
 * It draws what it is given and asks for the rest: no window of its own, no
 * fetching, no opinion on what to say when there is nothing — the screen
 * around it answers that, in its own words.
 *
 * Same frame as the teammates and the mission reference list: a strong rule
 * around, a strong rule under the titles, and the column that names the day
 * closed off from those that describe it.
 */
export function MoodsTable({ days, headcount, today }: MoodsTableProps) {
  return (
    <div className="[&_[data-slot=table-container]]:overflow-visible">
      <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
        <TableHeader className={TABLE_HEADER}>
          <TableRow>
            <TableHead className={`w-52 ${STRONG_SEPARATOR}`}>Jour</TableHead>
            {/* Without it, an empty row reads as a bad day rather than as a
                day nobody answered for. */}
            <TableHead className="w-24 text-right">Réponses</TableHead>
            <TableHead>Moral</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {days.map((day) => (
            <MoodDayRow
              key={day.day}
              day={day}
              headcount={headcount}
              isToday={day.day === today}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
