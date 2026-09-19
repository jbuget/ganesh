"use client";

import { UserRow } from "@/components/molecules/UserRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { UserResponse } from "@/lib/api/generated/model";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface UsersTableProps {
  /** The teammates to draw, already filtered and already in order. */
  users: UserResponse[];
  /** One reference time for every row, so « il y a 3 h » does not drift. */
  now: Date;
  onOpen: (userId: number) => void;
}

/**
 * The team as a table: who they are, what they may do, when they last came by.
 *
 * It draws what it is given and asks for the rest: no criteria of its own, no
 * fetching, no opinion on what to say when there is nothing — the screen around
 * it answers that, in its own words.
 *
 * It reads under the same frame as the mission reference list and the entry
 * grid: a strong rule around, a strong rule under the titles, and the column
 * that names the teammate closed off from those that describe them.
 */
export function UsersTable({ users, now, onOpen }: UsersTableProps) {
  return (
    // The shadcn container opens a scrolling context that would hold the header
    // inside the table: we neutralise it so the `sticky` latches onto the
    // page's scrolling area.
    <div className="[&_[data-slot=table-container]]:overflow-visible">
      <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
        <TableHeader className={TABLE_HEADER}>
          <TableRow>
            <TableHead className={STRONG_SEPARATOR}>Collaborateur</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Rôle</TableHead>
            <TableHead>Dernière connexion</TableHead>
            <TableHead>Statut</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {users.map((teammate) => (
            <UserRow
              key={teammate.id}
              user={teammate}
              now={now}
              onOpen={() => onOpen(teammate.id)}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
