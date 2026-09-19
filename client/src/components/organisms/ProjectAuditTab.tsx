"use client";

import { AuditLogRow } from "@/components/molecules/AuditLogRow";
import { Button } from "@/components/ui/button";
import { groupAuditByDay } from "@/lib/audit-log";
import { formatSpelledDate } from "@/lib/dates";
import { STRONG_RULE } from "@/lib/table-frame";
import { useProjectAudit } from "@/lib/use-project-audit";

interface ProjectAuditTabProps {
  projectId: number;
}

/**
 * Everything that ever happened to the mission.
 *
 * Nothing is sorted out: time declared sits beside a phase changed, because a
 * log that chose what deserves to be in it would no longer answer the question
 * one opens it with. Length is met by reading fifty lines at a time, and by
 * saying the day once above the gestures made that day.
 */
export function ProjectAuditTab({ projectId }: ProjectAuditTabProps) {
  const log = useProjectAudit(projectId);

  if (log.entries === null) {
    return <p className="py-6 text-sm text-slate-400">Chargement…</p>;
  }

  if (log.entries.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-slate-400">
        Rien n&apos;a encore été enregistré sur cette mission.
      </p>
    );
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
        {days.map(({ day, entries }) => (
          <section key={day}>
            {/* The day carries the strong rule above and below: it breaks the
                reading in two, where a line between two gestures only
                separates them. */}
            <h3
              className={`border-y bg-white px-3 py-1.5 text-xs font-medium text-slate-600 ${STRONG_RULE}`}
            >
              {formatSpelledDate(day)}
            </h3>
            <ul className="bg-slate-50">
              {entries.map((entry) => (
                <AuditLogRow key={entry.id} entry={entry} />
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
