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
import {
  NAMING_BUTTON,
  NAMING_CELL,
  NAMING_COLUMN,
  NAMING_CONTENT,
  STRONG_SEPARATOR,
  TABLE_FRAME,
  TABLE_HEADER,
} from "@/lib/table-frame";

/**
 * Who is there this week, and from where.
 *
 * The one screen the declaration exists for: reading a colleague's week one
 * panel at a time tells nobody whether Thursday is worth coming in for. The
 * count under each day is what one opens this for — a room to book, a lunch
 * to plan, a meeting to put where the people are.
 *
 * Everyone has a week: on site every day until they say otherwise, which is
 * the arrangement the team runs on. Nothing here is ever blank, and the count
 * under each day therefore covers the whole team.
 */
export function PresenceTable({
  users,
  onOpen,
}: {
  users: UserResponse[];
  /** A row opens the teammate, as on the accounts tab: the two tabs are two
      readings of one list, and a line means the same thing in both. */
  onOpen: (userId: number) => void;
}) {
  return (
    <div className="[&_[data-slot=table-container]]:overflow-visible">
      <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
        <TableHeader className={TABLE_HEADER}>
          <TableRow>
            <TableHead className={`${NAMING_COLUMN} ${STRONG_SEPARATOR}`}>
              Collaborateur
            </TableHead>
            {WEEKDAYS.map((day) => (
              <TableHead key={day.key} className="text-center">
                {day.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>

        <TableBody>
          {users.map((user) => (
            <TableRow
              key={user.id}
              onClick={() => onOpen(user.id)}
              className={`group cursor-pointer bg-slate-50 hover:bg-slate-100 ${
                user.is_active ? "" : "text-slate-400"
              }`}
            >
              <TableCell className={NAMING_CELL}>
                <span className={NAMING_CONTENT}>
                  <UserAvatar
                    initials={user.initials}
                    name={user.display_name}
                    dimmed={!user.is_active}
                  />
                  {/* The whole row responds to the mouse; this button gives
                      the same opening to the keyboard, without opening
                      twice. */}
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpen(user.id);
                    }}
                    className={NAMING_BUTTON}
                  >
                    {user.display_name}
                  </button>
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
            <TableCell
              className={`text-sm text-slate-500 ${NAMING_COLUMN} ${STRONG_SEPARATOR}`}
            >
              Sur site
            </TableCell>
            {WEEKDAYS.map((day) => {
              const onSite = users.filter(
                (user) => user.presence[day.key] === "ON_SITE",
              ).length;
              const present = users.filter(
                (user) => user.presence[day.key] !== "AWAY",
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
