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
 * Confirmation avant le retrait d'une mission qui porte du temps.
 *
 * Le total est annonce avant la decision : retirer la ligne efface les saisies
 * du mois, et rien ne permettrait de les retrouver ensuite.
 *
 * Une ligne vide ne passe pas par ici : il n'y a alors rien a perdre.
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
