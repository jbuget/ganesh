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
import { formatDecimalDays } from "@/lib/dates";

interface RemoveMissionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  label: string;
  total: number;
  onConfirm: () => Promise<void>;
}

/**
 * Confirmation before removing a mission that carries time.
 *
 * The total is announced before the decision: removing the row erases the
 * month's entries, and nothing would bring them back afterwards.
 *
 * An empty row does not go through here: there is then nothing to lose.
 */
export function RemoveMissionDialog({
  open,
  onOpenChange,
  label,
  total,
  onConfirm,
}: RemoveMissionDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Retirer {label} ?</AlertDialogTitle>
          <AlertDialogDescription>
            Cette mission porte {formatDecimalDays(total)} day(s) saisi(s) sur le mois.
            Les retirer est définitif.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel>Annuler</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-red-600 text-white hover:bg-red-700"
          >
            Retirer la mission
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
