"use client";

import { SortableColumnHeader } from "@/components/atoms/SortableColumnHeader";
import { UserRow } from "@/components/molecules/UserRow";
import { Table, TableBody, TableHeader, TableRow } from "@/components/ui/table";
import type { UserResponse } from "@/lib/api/generated/model";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";
import type { UserSort, UserSortColumn } from "@/lib/user-sort";

interface UsersTableProps {
  /** The teammates to draw, already filtered and already in order. */
  users: UserResponse[];
  sorted: UserSort;
  onSort: (column: UserSortColumn) => void;
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
export function UsersTable({ users, sorted, onSort, now, onOpen }: UsersTableProps) {
  return (
    // The shadcn container opens a scrolling context that would hold the header
    // inside the table: we neutralise it so the `sticky` latches onto the
    // page's scrolling area.
    <div className="[&_[data-slot=table-container]]:overflow-visible">
      <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
        <TableHeader className={TABLE_HEADER}>
          <TableRow>
            {/* Every column sorts: four of the five carry an order the reader
                already has in mind — the alphabet, the ladder of roles, how
                long ago someone came by, whether the access is open. */}
            <SortableColumnHeader
              column="name"
              label="Collaborateur"
              sorted={sorted}
              onToggle={onSort}
              className={STRONG_SEPARATOR}
            />
            <SortableColumnHeader
              column="email"
              label="Email"
              sorted={sorted}
              onToggle={onSort}
            />
            <SortableColumnHeader
              column="role"
              label="Rôle"
              sorted={sorted}
              onToggle={onSort}
            />
            <SortableColumnHeader
              column="login"
              label="Dernière connexion"
              sorted={sorted}
              onToggle={onSort}
            />
            <SortableColumnHeader
              column="status"
              label="Statut"
              sorted={sorted}
              onToggle={onSort}
            />
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
