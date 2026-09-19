"use client";

import { useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { formatTotal } from "@/lib/dates";

interface ValidateMonthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  month: string;
  totalEntered: number;
  workingDays: number;
  onConfirm: () => Promise<void>;
}

/**
 * Confirmation before locking a month.
 *
 * The summary is shown before the decision: checking completeness is what makes
 * the data good, better than a block that would push people to fill in
 * anything.
 */
export function ValidateMonthDialog({
  open,
  onOpenChange,
  month,
  totalEntered,
  workingDays,
  onConfirm,
}: ValidateMonthDialogProps) {
  const missing = Math.max(0, workingDays - totalEntered);
  const [busy, setBusy] = useState(false);

  /**
   * The dialog closes itself once the month is locked: nothing in the
   * confirmation closes the window, and a failure must stay before the eyes.
   */
  async function confirm() {
    if (busy) return;
    setBusy(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="capitalize">Valider {month} ?</AlertDialogTitle>
          <AlertDialogDescription>
            Après validation, vous ne pourrez plus modifier ce mois. Seul un manager
            pourra le rouvrir.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <dt className="text-muted-foreground">Total saisi</dt>
          <dd className="text-right font-medium">
            {formatTotal(totalEntered)} jour(s)
          </dd>
          <dt className="text-muted-foreground">Jours ouvrés</dt>
          <dd className="text-right font-medium">{workingDays} jours</dd>
        </dl>

        {missing > 0 && (
          <p className="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Il manque {formatTotal(missing)} jour(s) pour couvrir le mois.
          </p>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel>Annuler</AlertDialogCancel>
          <AlertDialogAction onClick={confirm} disabled={busy}>
            Valider
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
