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

interface DeactivateUserDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  name: string;
  onConfirm: () => void | Promise<void>;
}

/**
 * Confirmation before cutting off a user's access.
 *
 * Nothing is erased: past entries stay and go on feeding the per-project
 * totals. Saying so here saves hesitating over a reversible action.
 *
 * Restoring, on the other hand, needs no confirmation: it takes nothing away
 * from anyone.
 */
export function DeactivateUserDialog({
  open,
  onOpenChange,
  name,
  onConfirm,
}: DeactivateUserDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Désactiver {name} ?</AlertDialogTitle>
          <AlertDialogDescription>
            Ce compte n&apos;aura plus accès à Timesheet, et disparaîtra des listes. Ses
            saisies passées sont conservées. Un manager peut le réactiver à tout moment.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel>Annuler</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-red-600 text-white hover:bg-red-700"
          >
            Désactiver
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
