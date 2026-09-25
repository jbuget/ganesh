"use client";

import { RequestRow } from "@/components/molecules/RequestRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { RequestResponse } from "@/lib/api/generated/model";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface RequestsTableProps {
  /** The needs to draw, already filtered. */
  requests: RequestResponse[];
  onOpen: (requestId: number) => void;
}

/**
 * The needs the company has expressed, as a table.
 *
 * It draws what it is given and asks for the rest: no criteria of its own, no
 * fetching, no opinion on what to say when there is nothing — the screen
 * around it answers that, in its own words.
 *
 * Same frame as the mission reference list and the teammates: a strong rule
 * around, a strong rule under the titles, and the column that names the need
 * closed off from those that describe it.
 */
export function RequestsTable({ requests, onOpen }: RequestsTableProps) {
  return (
    // The shadcn container opens a scrolling context that would hold the header
    // inside the table: we neutralise it so the `sticky` latches onto the
    // page's scrolling area.
    <div className="[&_[data-slot=table-container]]:overflow-visible">
      <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
        <TableHeader className={TABLE_HEADER}>
          <TableRow>
            <TableHead className={STRONG_SEPARATOR}>Demande</TableHead>
            <TableHead>Demandeur</TableHead>
            <TableHead>Départements</TableHead>
            <TableHead>Sponsors</TableHead>
            <TableHead>État</TableHead>
            <TableHead>Soumise le</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {requests.map((request) => (
            <RequestRow
              key={request.id}
              request={request}
              onOpen={() => onOpen(request.id)}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
