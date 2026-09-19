"use client";

import { AuditLogRow } from "@/components/molecules/AuditLogRow";
import { Button } from "@/components/ui/button";
import { groupAuditByDay } from "@/lib/audit-log";
import { formatSpelledDate } from "@/lib/dates";
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
 *
 * Drawn without a frame, where the tables of the application carry one. A
 * table is a grid one reads across, and the strong rule says where it stops;
 * this is a column of sentences read from the top down, and ruling it would
 * fence off something that has no columns to line up. The day headings carry
 * the rhythm on their own.
 */
export function ProjectAuditTab({ projectId }: ProjectAuditTabProps) {
  const log = useProjectAudit(projectId);

  if (log.entries === null) {
    return <p className="py-6 text-sm text-slate-400">Chargement…</p>;
  }

  if (log.entries.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-slate-400">
        Rien n&apos;a encore été enregistré sur ce projet.
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

      <div className="space-y-4">
        {days.map(({ day, entries }) => (
          <section key={day}>
            {/* The day is what one navigates by, so it is set apart by weight
                and by the air above it rather than by a rule. */}
            <h3 className="mb-1 text-xs font-semibold text-slate-500">
              {formatSpelledDate(day)}
            </h3>
            <ul>
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
