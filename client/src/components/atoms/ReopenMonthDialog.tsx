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

interface ReopenMonthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  month: string;
  /** Whose month it is, when it is not one's own. */
  teammate: string | null;
  onConfirm: () => Promise<void>;
}

/**
 * Confirmation before giving a validated month back to entry.
 *
 * Reopening undoes a commitment somebody made: the window says whose month it
 * is and that the move is recorded, which is what the lock rests on — the
 * traceability of the gesture, not a permanent bolt.
 */
export function ReopenMonthDialog({
  open,
  onOpenChange,
  month,
  teammate,
  onConfirm,
}: ReopenMonthDialogProps) {
  const [busy, setBusy] = useState(false);

  /**
   * The dialog closes itself once the month is open again: a refusal from the
   * API must stay before the eyes rather than vanish with the window.
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
          <AlertDialogTitle className="capitalize">Rouvrir {month} ?</AlertDialogTitle>
          <AlertDialogDescription>
            {teammate
              ? `Le mois de ${teammate} redeviendra modifiable, et devra être validé à nouveau.`
              : "Votre mois redeviendra modifiable, et devra être validé à nouveau."}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <p className="text-muted-foreground text-sm">
          Cette réouverture sera inscrite au journal, à votre nom.
        </p>

        <AlertDialogFooter>
          <AlertDialogCancel>Annuler</AlertDialogCancel>
          <AlertDialogAction onClick={confirm} disabled={busy}>
            Rouvrir
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
