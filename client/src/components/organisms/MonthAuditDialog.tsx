"use client";

import { AuditLogList } from "@/components/organisms/AuditLogList";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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

        <AuditLogList
          log={log}
          reading={{ read: "month" }}
          emptiness="Rien n'a encore été enregistré sur ce mois."
        />
      </DialogContent>
    </Dialog>
  );
}
