"use client";

import { AuditLogRow } from "@/components/molecules/AuditLogRow";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { groupAuditByDay } from "@/lib/audit-log";
import { formatSpelledDate } from "@/lib/dates";
import { STRONG_RULE } from "@/lib/table-frame";
import { useMonthAudit } from "@/lib/use-month-audit";

interface MonthAuditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** First day of the month being read, as the API names it. */
  month: string;
  /** The month as the screen spells it, for the title. */
  label: string;
  /** Whose month it is. Null while the screen does not know yet. */
  userId: number | null;
  /** Whose month it is, when it is not one's own. */
  teammate: string | null;
}

/**
 * The life of one month.
 *
 * A grid says what a month holds; it never says how it got there. Anyone may
 * fill in a colleague's open month, and a manager may give a validated one
 * back to entry: this is where those gestures are read back, signed and dated.
 *
 * Each line names the mission it was about, which the grid carries in its rows
 * and a log read out of it would otherwise lose. What it does not repeat is
 * whose month it is and which one — the window above says both.
 */
export function MonthAuditDialog({
  open,
  onOpenChange,
  month,
  label,
  userId,
  teammate,
}: MonthAuditDialogProps) {
  const log = useMonthAudit(month, userId);
  const days = groupAuditByDay(log.entries ?? []);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          {/* No `capitalize` here, unlike the screens that open on the month:
              it capitalises every word, and the month is read mid-sentence —
              « Historique De Septembre 2026 » is not French. */}
          <DialogTitle>Historique de {label}</DialogTitle>
          <DialogDescription>
            {teammate
              ? `Ce qui a été fait sur le mois de ${teammate}, du plus récent au plus ancien.`
              : "Ce qui a été fait sur ce mois, du plus récent au plus ancien."}
          </DialogDescription>
        </DialogHeader>

        {log.entries === null && <p className="text-sm text-slate-400">Chargement…</p>}

        {log.entries?.length === 0 && (
          <p className="py-6 text-center text-sm text-slate-400">
            Rien n&apos;a encore été enregistré sur ce mois.
          </p>
        )}

        {days.length > 0 && (
          <div className="space-y-3">
            {/* The tally before the lines: it says how far the log goes, which
                a page of fifty on its own never could. */}
            <p className="text-xs text-slate-500">
              {log.total > 1 ? `${log.total} gestes enregistrés` : "1 geste enregistré"}
            </p>

            <div className={`overflow-hidden border ${STRONG_RULE}`}>
              {days.map(({ day, entries }, rank) => (
                <section key={day}>
                  {/* The day carries the strong rule above and below: it breaks
                      the reading in two, where a line between two gestures only
                      separates them. The first one does without the rule above,
                      the frame already closing the log there. */}
                  <h3
                    className={`border-b bg-white px-3 py-1.5 text-xs font-medium text-slate-600 ${STRONG_RULE} ${rank > 0 ? "border-t" : ""}`}
                  >
                    {formatSpelledDate(day)}
                  </h3>
                  <ul className="bg-slate-50">
                    {entries.map((entry) => (
                      <AuditLogRow
                        key={entry.id}
                        entry={entry}
                        reading={{ read: "month" }}
                      />
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
        )}
      </DialogContent>
    </Dialog>
  );
}
