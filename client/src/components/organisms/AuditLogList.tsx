"use client";

import { AuditLogRow } from "@/components/molecules/AuditLogRow";
import { Button } from "@/components/ui/button";
import { type AuditReading, groupAuditByDay } from "@/lib/audit-log";
import { formatSpelledDate } from "@/lib/dates";
import { STRONG_RULE } from "@/lib/table-frame";
import type { PagedAuditLog } from "@/lib/use-paged-audit";

interface AuditLogListProps {
  log: PagedAuditLog;
  /** Which log this is, which decides how each gesture is said. */
  reading: AuditReading;
  /** Said where the log is empty — what it is the log of is the screen's own. */
  emptiness: string;
}

/**
 * A log, however it was read and whatever it is the log of.
 *
 * A mission's journal and a month's history show the same thing — who did what,
 * when — and two screens that read alike must not be able to drift apart. What
 * each one keeps for itself is what it is the log of: the sentence a gesture is
 * said in, and what to say when nothing has happened yet.
 *
 * Length is met by reading fifty lines at a time, and by saying the day once
 * above the gestures made that day.
 */
export function AuditLogList({ log, reading, emptiness }: AuditLogListProps) {
  if (log.entries === null) {
    return <p className="py-6 text-sm text-slate-400">Chargement…</p>;
  }

  if (log.entries.length === 0) {
    return <p className="py-6 text-center text-sm text-slate-400">{emptiness}</p>;
  }

  const days = groupAuditByDay(log.entries);

  return (
    <div className="space-y-3">
      {/* The tally before the lines: it says how far the log goes, which a page
          of fifty on its own never could. */}
      <p className="text-xs text-slate-500">
        {log.total > 1 ? `${log.total} gestes enregistrés` : "1 geste enregistré"}
      </p>

      <div className={`overflow-hidden border ${STRONG_RULE}`}>
        {days.map(({ day, entries }, rank) => (
          <section key={day}>
            {/* The day carries the strong rule above and below: it breaks the
                reading in two, where a line between two gestures only
                separates them.

                The first one does without the rule above: the frame already
                closes the log there, and the two lines sitting side by side
                read as one thick, crooked border. */}
            <h3
              className={`border-b bg-white px-3 py-1.5 text-xs font-medium text-slate-600 ${STRONG_RULE} ${rank > 0 ? "border-t" : ""}`}
            >
              {formatSpelledDate(day)}
            </h3>
            <ul className="bg-slate-50">
              {entries.map((entry) => (
                <AuditLogRow key={entry.id} entry={entry} reading={reading} />
              ))}
            </ul>
          </section>
        ))}
      </div>

      {log.hasMore && (
        <div className="flex justify-center">
          <Button
            size="sm"
            variant="outline"
            className="cursor-pointer"
            disabled={log.busy}
            onClick={() => void log.loadMore()}
          >
            {log.busy ? "Chargement…" : "Voir plus"}
          </Button>
        </div>
      )}
    </div>
  );
}
