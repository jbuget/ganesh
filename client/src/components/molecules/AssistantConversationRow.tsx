"use client";

import { ThumbsDown, ThumbsUp } from "lucide-react";

import { TableCell, TableRow } from "@/components/ui/table";
import type { ConversationSummaryResponse } from "@/lib/api/generated/model";
import { formatParisDateTime } from "@/lib/instants";
import { NAMING_BUTTON, NAMING_CELL, NAMING_CONTENT } from "@/lib/table-frame";

interface AssistantConversationRowProps {
  conversation: ConversationSummaryResponse;
  askerName: string;
  onOpen: () => void;
}

/**
 * A conversation, named by the question that opened it.
 *
 * The question is what one scans the list for — « où en est », « quand sera
 * libre » — so it is the anchor of the line, and the rest says whether it
 * went well and whether anybody has read it yet.
 */
export function AssistantConversationRow({
  conversation,
  askerName,
  onOpen,
}: AssistantConversationRowProps) {
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
            title={conversation.first_question}
          >
            {conversation.first_question}
          </button>
        </span>
      </TableCell>

      <TableCell className="py-2 text-slate-600">{askerName}</TableCell>

      <TableCell className="py-2 text-slate-500 tabular-nums">
        {formatParisDateTime(conversation.last_asked_at)}
      </TableCell>

      <TableCell className="py-2 text-right text-slate-600 tabular-nums">
        {conversation.exchange_count}
      </TableCell>

      <TableCell className="py-2 text-slate-600">
        <span className="flex items-center gap-3 tabular-nums">
          {conversation.helpful > 0 && (
            <span className="flex items-center gap-1" title="Jugées utiles">
              <ThumbsUp aria-label="Utiles" className="size-3.5" />
              {conversation.helpful}
            </span>
          )}
          {conversation.unhelpful > 0 && (
            <span className="flex items-center gap-1" title="Jugées pas utiles">
              <ThumbsDown aria-label="Pas utiles" className="size-3.5" />
              {conversation.unhelpful}
            </span>
          )}
          {conversation.helpful + conversation.unhelpful === 0 && (
            <span className="text-slate-400">—</span>
          )}
        </span>
      </TableCell>

      <TableCell className="py-2 text-slate-500 tabular-nums">
        {conversation.annotated === 0 ? (
          <span className="text-slate-400">—</span>
        ) : (
          `${conversation.annotated} / ${conversation.exchange_count}`
        )}
      </TableCell>
    </TableRow>
  );
}
