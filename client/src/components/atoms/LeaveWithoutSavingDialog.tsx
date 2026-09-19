"use client";

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

interface LeaveWithoutSavingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The simulation being edited, when it is one that was saved. */
  simulationName: string | null;
  /** Goes ahead and loses the work. */
  onDiscard: () => void;
}

/**
 * The question asked before unsaved work is thrown away.
 *
 * Staying is the safe answer, so staying is the one the keyboard lands on:
 * whoever is halfway through a scenario and hits Enter out of habit must not
 * lose it for that. Leaving is spelled out — « Quitter sans enregistrer » —
 * rather than left to a bare « OK » nobody reads.
 */
export function LeaveWithoutSavingDialog({
  open,
  onOpenChange,
  simulationName,
  onDiscard,
}: LeaveWithoutSavingDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Modifications non enregistrées</AlertDialogTitle>
          <AlertDialogDescription>
            {simulationName
              ? `Les modifications apportées à « ${simulationName} » ne sont pas enregistrées. Si vous partez maintenant, elles seront perdues.`
              : "Cette simulation n'a jamais été enregistrée. Si vous partez maintenant, elle sera perdue."}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel className="cursor-pointer">Rester</AlertDialogCancel>
          <AlertDialogAction className="cursor-pointer" onClick={onDiscard}>
            Quitter sans enregistrer
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
