"use client";

import { MoodMark } from "@/components/atoms/MoodMark";
import { TableCell, TableRow } from "@/components/ui/table";
import type { DayMoodsResponse } from "@/lib/api/generated/model";
import { formatWeekdayDate } from "@/lib/dates";
import { STRONG_SEPARATOR } from "@/lib/table-frame";
import { useCursorTooltip } from "@/lib/use-cursor-tooltip";

interface MoodDayRowProps {
  day: DayMoodsResponse;
  /** Active teammates: three answers out of four is not three out of twenty. */
  headcount: number;
  isToday: boolean;
}

/**
 * One day of the window: who answered, and what they said.
 *
 * The moods come in already ordered, best first: the shape of the day is what
 * one reads before any single answer — where the row turns from green to
 * orange says more than any one face in it.
 *
 * Initials cannot be guessed, so the name comes at the cursor, as it does on a
 * mission's contributors. One tooltip serves the whole row rather than one per
 * face: twenty listeners on a line would each fire on their own.
 */
export function MoodDayRow({ day, headcount, isToday }: MoodDayRowProps) {
  const { tooltip, follow, leave } = useCursorTooltip();

  return (
    // The row takes the page tint and the date cell stays white, one step
    // behind: the day reads as the anchor of the line rather than as its first
    // column, exactly as the teammate does on the users table.
    <TableRow className="group bg-slate-50 hover:bg-slate-100">
      <TableCell
        className={`bg-white py-2 align-top group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
      >
        <span className="block text-sm text-slate-700 first-letter:uppercase">
          {formatWeekdayDate(day.day)}
        </span>
        {isToday && <span className="text-xs text-slate-400">aujourd&apos;hui</span>}
      </TableCell>

      <TableCell className="py-2 text-right align-top text-sm tabular-nums text-slate-500">
        {day.participation}
        <span className="text-slate-300"> / {headcount}</span>
      </TableCell>

      <TableCell className="py-2 align-top" onMouseLeave={leave}>
        {day.moods.length === 0 ? (
          <span className="text-sm text-slate-400">Personne n&apos;a répondu</span>
        ) : (
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
            {day.moods.map((signed) => (
              <span
                key={signed.author.id}
                onMouseMove={(event) => follow(event, signed.author.display_name)}
              >
                <MoodMark level={signed.level} initials={signed.author.initials} />
              </span>
            ))}
          </div>
        )}
        {/* Mounted in a portal on `body`, but kept inside the cell: a
            portal placed straight under `<tr>` is a child the row has no
            slot for. */}
        {tooltip}
      </TableCell>
    </TableRow>
  );
}
