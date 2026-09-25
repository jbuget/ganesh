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

interface WithdrawActivityDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  label: string;
  /** Days already declared on it, across every month and every teammate. */
  entries: number;
  onConfirm: () => void | Promise<void>;
}

/**
 * Taking an activity out of what a month can be declared on.
 *
 * Two gestures behind one button, and which one it is depends on what the
 * activity carries. An activity nobody declared on is deleted: it is the
 * trade added by mistake, and leaving it archived would clutter the list for
 * nothing.
 *
 * One carrying days is archived instead, never deleted — a validated month is
 * immutable, and deleting would empty cells inside one without anybody
 * reopening it. The days stay readable and the line can come back; only what
 * one can still declare on shrinks. The dialog says so rather than leaving
 * the reader to guess which of the two just happened.
 */
export function WithdrawActivityDialog({
  open,
  onOpenChange,
  label,
  entries,
  onConfirm,
}: WithdrawActivityDialogProps) {
  const carries = entries > 0;
  const days = entries > 1 ? "saisies" : "saisie";

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {carries ? `Archiver « ${label} » ?` : `Supprimer « ${label} » ?`}
          </AlertDialogTitle>
          <AlertDialogDescription>
            {carries
              ? `Cette activité porte ${entries} ${days}. Rien n'est effacé : les jours déjà déclarés restent lisibles dans les feuilles de temps, y compris dans les mois validés. Seule la possibilité d'y saisir du temps disparaît, et l'activité peut être rouverte.`
              : "Cette activité n'a jamais porté de temps. Sa suppression est définitive, mais elle n'emporte rien d'autre qu'elle-même."}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel className="cursor-pointer">Annuler</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className={
              carries
                ? "cursor-pointer"
                : "cursor-pointer bg-red-600 text-white hover:bg-red-700"
            }
          >
            {carries ? "Archiver l'activité" : "Supprimer l'activité"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
