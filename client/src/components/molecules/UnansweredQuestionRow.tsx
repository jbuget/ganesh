"use client";

import { TableCell, TableRow } from "@/components/ui/table";
import type { UnansweredQuestionResponse } from "@/lib/api/generated/model";
import { seconds, whyUnansweredLabel } from "@/lib/assistant-study";
import { formatParisDateTime } from "@/lib/instants";
import { NAMING_BUTTON, NAMING_CELL, NAMING_CONTENT } from "@/lib/table-frame";

interface UnansweredQuestionRowProps {
  question: UnansweredQuestionResponse;
  askerName: string;
  onOpen: () => void;
}

/** A question that came back with no answer, named by what was asked. */
export function UnansweredQuestionRow({
  question,
  askerName,
  onOpen,
}: UnansweredQuestionRowProps) {
  return (
    <TableRow
      onClick={onOpen}
      className="group cursor-pointer bg-slate-50 hover:bg-slate-100"
    >
      <TableCell className={`${NAMING_CELL} max-w-[28rem]`}>
        <span className={NAMING_CONTENT}>
          {/* The row responds to the mouse; this button gives the same opening
              to the keyboard, without opening twice. */}
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onOpen();
            }}
            className={`${NAMING_BUTTON} truncate`}
            title={question.question}
          >
            {question.question}
          </button>
        </span>
      </TableCell>
      <TableCell className="py-2 text-slate-600">{askerName}</TableCell>
      <TableCell className="py-2 text-slate-500 tabular-nums">
        {formatParisDateTime(question.asked_at)}
      </TableCell>
      <TableCell className="py-2 text-slate-600">
        {whyUnansweredLabel(question.reason)}
      </TableCell>
      <TableCell className="py-2 text-right text-slate-600 tabular-nums">
        {question.consultations.length}
      </TableCell>
      <TableCell className="py-2 text-right text-slate-500 tabular-nums">
        {seconds(question.elapsed_ms)}
      </TableCell>
    </TableRow>
  );
}
