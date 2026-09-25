"use client";

import { RequestStateMark } from "@/components/atoms/RequestStateMark";
import { TableCell, TableRow } from "@/components/ui/table";
import type { RequestResponse } from "@/lib/api/generated/model";
import { departmentLabel } from "@/lib/departments";
import { formatSpelledDate } from "@/lib/dates";
import { parisDay } from "@/lib/instants";
import { STRONG_SEPARATOR } from "@/lib/table-frame";

interface RequestRowProps {
  request: RequestResponse;
  onOpen: () => void;
}

/**
 * A need: what it is called, who asked for it, and where it stands.
 *
 * The row compares, it does not arbitrate: like every other list of the
 * application it opens one thing — the panel, which is the only place a need
 * is read whole and weighed. A decision taken from a row would be a decision
 * taken without having read it.
 */
export function RequestRow({ request, onOpen }: RequestRowProps) {
  return (
    <TableRow
      onClick={onOpen}
      className="group cursor-pointer bg-slate-50 hover:bg-slate-100"
    >
      <TableCell
        className={`bg-white py-2 group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
      >
        {/* The whole row responds to the mouse; this button gives the same
            opening to the keyboard, without opening twice. */}
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onOpen();
          }}
          className="min-w-0 cursor-pointer truncate text-left font-medium"
        >
          {request.title}
        </button>
      </TableCell>

      <TableCell className="py-2">{request.requester.label}</TableCell>

      <TableCell className="py-2 text-slate-600">
        {request.departments.map(departmentLabel).join(", ")}
      </TableCell>

      <TableCell className="py-2 text-slate-600">
        {request.sponsors.map((sponsor) => sponsor.label).join(", ")}
      </TableCell>

      <TableCell className="py-2">
        <RequestStateMark value={request.state} />
      </TableCell>

      <TableCell className="py-2 tabular-nums text-slate-600">
        {/* The day it was handed over, not the day it was opened: a draft
            nobody submitted has no date the team has any use for. */}
        {request.submitted_at ? formatSpelledDate(parisDay(request.submitted_at)) : "—"}
      </TableCell>
    </TableRow>
  );
}
