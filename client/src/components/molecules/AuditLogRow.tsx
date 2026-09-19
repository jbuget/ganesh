"use client";

import { ArrowRight } from "lucide-react";

import type { AuditLogEntryResponse } from "@/lib/api/generated/model";
import { auditSentence } from "@/lib/audit-log";

interface AuditLogRowProps {
  entry: AuditLogEntryResponse;
}

/** The time of day, on the clock the server recorded it by. */
function atTime(iso: string): string {
  const [hours, minutes] = iso.slice(11, 16).split(":");
  return `${hours}:${minutes}`;
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
 */
export function AuditLogRow({ entry }: AuditLogRowProps) {
  const sentence = auditSentence(entry);
  // An account removed leaves its gestures behind: the log says so rather than
  // signing them to nobody in silence.
  const actor = entry.actor;

  return (
    <li className="flex items-baseline gap-3 border-b border-slate-200 px-3 py-2 last:border-b-0">
      <span className="w-10 shrink-0 text-xs tabular-nums text-slate-400">
        {atTime(entry.at)}
      </span>

      <span className="min-w-0 flex-1">
        <span className="block text-sm text-slate-700">
          <span className="font-medium text-slate-900">
            {actor?.display_name ?? "Compte supprimé"}
          </span>{" "}
          {sentence.action}
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
