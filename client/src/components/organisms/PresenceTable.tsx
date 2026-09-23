"use client";

import { PresenceMark } from "@/components/atoms/PresenceMark";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { UserResponse } from "@/lib/api/generated/model";
import { WEEKDAYS, sayDay } from "@/lib/presence";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

/**
 * Who is there this week, and from where.
 *
 * The one screen the declaration exists for: reading a colleague's week one
 * panel at a time tells nobody whether Thursday is worth coming in for. The
 * count under each day is what one opens this for — a room to book, a lunch
 * to plan, a meeting to put where the people are.
 *
 * A week nobody declared is left blank rather than drawn as five absences:
 * one is something nobody has said yet, the other is something somebody said,
 * and an office that merely looks empty would be read as an empty office.
 */
export function PresenceTable({ users }: { users: UserResponse[] }) {
  const declared = users.filter((user) => user.presence);

  return (
    <div className="[&_[data-slot=table-container]]:overflow-visible">
      <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
        <TableHeader className={TABLE_HEADER}>
          <TableRow>
            <TableHead className={STRONG_SEPARATOR}>Collaborateur</TableHead>
            {WEEKDAYS.map((day) => (
              <TableHead key={day.key} className="text-center">
                {day.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>

        <TableBody>
          {users.map((user) => (
            <TableRow key={user.id} className="bg-slate-50 hover:bg-slate-100">
              <TableCell
                className={`bg-white group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
              >
                <span className="flex items-center gap-2">
                  <UserAvatar
                    initials={user.initials}
                    name={user.display_name}
                    dimmed={!user.is_active}
                  />
                  <span className="truncate">{user.display_name}</span>
                </span>
              </TableCell>

              {WEEKDAYS.map((day) => (
                <TableCell key={day.key} className="text-center">
                  {user.presence ? (
                    <PresenceMark day={user.presence[day.key]} labelled={false} />
                  ) : null}
                  <span className="sr-only">
                    {user.presence
                      ? `${day.label} : ${sayDay(user.presence[day.key])}`
                      : `${day.label} : non renseigné`}
                  </span>
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>

        <TableFooter className="bg-white">
          <TableRow>
            <TableCell className={`text-sm text-slate-500 ${STRONG_SEPARATOR}`}>
              Sur site
            </TableCell>
            {WEEKDAYS.map((day) => {
              const onSite = declared.filter(
                (user) => user.presence?.[day.key] === "ON_SITE",
              ).length;
              const present = declared.filter(
                (user) => user.presence?.[day.key] !== "AWAY",
              ).length;

              return (
                <TableCell key={day.key} className="text-center">
                  <span className="font-semibold tabular-nums">{onSite}</span>
                  <span className="block text-[11px] text-slate-400">
                    sur {present} présent{present > 1 ? "s" : ""}
                  </span>
                </TableCell>
              );
            })}
          </TableRow>
        </TableFooter>
      </Table>
    </div>
  );
}
