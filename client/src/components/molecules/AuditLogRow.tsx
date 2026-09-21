"use client";

import { ArrowRight } from "lucide-react";

import type { AuditLogEntryResponse } from "@/lib/api/generated/model";
import { type AuditReading, auditSentence } from "@/lib/audit-log";
import { formatParisTime } from "@/lib/instants";

interface AuditLogRowProps {
  entry: AuditLogEntryResponse;
  /** Which log the line is read in. A mission's own, unless said otherwise. */
  reading?: AuditReading;
}

/**
 * One gesture, read as a sentence.
 *
 * The time anchors the line on the left, the name says who, and the change —
 * when there is a before and an after — sits on its own line underneath: a
 * value is often long enough to push the sentence off the panel, and what is
 * being read first is who did what.
 *
 * No avatar: an initials badge repeated on every line marks nothing, the name
 * being right beside it on the same line.
 *
 * The mission closes the sentence where the line carries one — which happens
 * on a month's log, never on a mission's, where it would be the same name on
 * every row.
 */
export function AuditLogRow({ entry, reading }: AuditLogRowProps) {
  const sentence = auditSentence(entry, reading);
  // An account removed leaves its gestures behind: the log says so rather than
  // signing them to nobody in silence.
  const actor = entry.actor;

  return (
    <li className="flex items-baseline gap-3 border-b border-slate-200 px-3 py-2 last:border-b-0">
      <span className="w-10 shrink-0 text-xs tabular-nums text-slate-400">
        {formatParisTime(entry.at)}
      </span>

      <span className="min-w-0 flex-1">
        <span className="block text-sm text-slate-700">
          <span className="font-medium text-slate-900">
            {actor?.display_name ?? "Compte supprimé"}
          </span>{" "}
          {sentence.action}
          {entry.project && (
            <>
              <span className="text-slate-400" aria-hidden>
                {" · "}
              </span>
              <span className="text-slate-500">{entry.project.label}</span>
            </>
          )}
        </span>

        {sentence.to !== undefined && (
          <span className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-500">
            <span className="min-w-0 truncate line-through decoration-slate-300">
              {sentence.from}
            </span>
            <ArrowRight className="size-3 shrink-0 text-slate-400" aria-hidden />
            <span className="min-w-0 truncate text-slate-700">{sentence.to}</span>
          </span>
        )}
      </span>
    </li>
  );
}
