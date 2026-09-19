"use client";

import { MoodLegend } from "@/components/atoms/MoodLegend";
import { MoodTrendRow } from "@/components/molecules/MoodTrendRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DayMoodsResponse } from "@/lib/api/generated/model";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface MoodTrendsTableProps {
  /** The days of the window, the most recent first. */
  days: DayMoodsResponse[];
  headcount: number;
  today: string;
}

/**
 * The fortnight summed up: how each day was spread, and where it landed.
 *
 * The legend comes first and not last: the bars are read as surfaces, and a
 * shade one has to guess is read twice.
 *
 * Same frame as the record beside it: two tabs of one screen must not look
 * like two screens.
 */
export function MoodTrendsTable({ days, headcount, today }: MoodTrendsTableProps) {
  return (
    <div className="space-y-3">
      <MoodLegend />

      <div className="[&_[data-slot=table-container]]:overflow-visible">
        <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
          <TableHeader className={TABLE_HEADER}>
            <TableRow>
              <TableHead className={`w-52 ${STRONG_SEPARATOR}`}>Jour</TableHead>
              <TableHead className="w-24 text-right">Réponses</TableHead>
              <TableHead>Répartition</TableHead>
              <TableHead className="w-64">Moyenne</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {days.map((day) => (
              <MoodTrendRow
                key={day.day}
                day={day}
                headcount={headcount}
                isToday={day.day === today}
              />
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
