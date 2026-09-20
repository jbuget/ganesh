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

interface RegenerateDigestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  month: string;
  onConfirm: () => void | Promise<void>;
}

/**
 * Confirmation before asking for a month a second time.
 *
 * Nothing is lost — the version being read is kept, and stays reachable — but
 * the month will read as the new one from now on, and everyone else will see
 * that one. Worth a moment's pause; not worth a warning.
 */
export function RegenerateDigestDialog({
  open,
  onOpenChange,
  month,
  onConfirm,
}: RegenerateDigestDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Regénérer le digest de {month} ?</AlertDialogTitle>
          <AlertDialogDescription>
            Une nouvelle version sera écrite à partir du journal tel qu&apos;il est
            aujourd&apos;hui. La version actuelle est conservée et reste consultable,
            mais le mois s&apos;affichera désormais dans la nouvelle.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel>Annuler</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}>Regénérer</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
