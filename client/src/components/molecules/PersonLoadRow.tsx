"use client";

import { PersonLoadCell } from "@/components/atoms/PersonLoadCell";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import { TableCell, TableRow } from "@/components/ui/table";
import type { PersonLoadResponse } from "@/lib/api/generated/model";
import { formatDecimalDays, formatWeek } from "@/lib/dates";
import { STRONG_SEPARATOR } from "@/lib/table-frame";

interface PersonLoadRowProps {
  person: PersonLoadResponse;
}

/**
 * One person's diary across the horizon.
 *
 * The two figures on the left answer the question steering actually asks: how
 * much room is left, and from when. « Alice est prise » steers nothing;
 * « Alice se libère la semaine du 12 octobre » does.
 */
export function PersonLoadRow({ person }: PersonLoadRowProps) {
  return (
    <TableRow className="group bg-slate-50 hover:bg-slate-100">
      {/* The pinned column names the row, and stays white where the row takes
          the page's tint: the subject reads as the line's anchor. */}
      <TableCell
        className={`sticky left-0 z-10 bg-white group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
      >
        <div className="flex items-center gap-2">
          <UserAvatar initials={person.user.initials} name={person.user.display_name} />
          <span className="truncate text-sm text-slate-800">
            {person.user.display_name}
          </span>
        </div>
      </TableCell>

      <TableCell className="text-right text-sm text-slate-600 tabular-nums">
        {formatDecimalDays(person.free_days)}
      </TableCell>

      <TableCell className="whitespace-nowrap text-sm text-slate-600">
        {person.first_free_week ? (
          `Semaine du ${formatWeek(person.first_free_week)}`
        ) : (
          <span className="text-slate-400">Aucune</span>
        )}
      </TableCell>

      {person.weeks.map((week) => (
        <TableCell key={week.week} className="px-1">
          <PersonLoadCell
            capacity={week.capacity}
            booked={week.booked}
            projected={week.projected}
            reserved={week.reserved}
            isOverloaded={week.is_overloaded}
          />
        </TableCell>
      ))}
    </TableRow>
  );
}
