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

interface DeleteUpdateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void | Promise<void>;
}

/**
 * Confirmation before withdrawing one's own update.
 *
 * The gesture is one click away from the pencil beside it, and unlike a
 * correction it cannot be undone: the text and the signs it drew go for good.
 * What stays is said too, so nobody withdraws an update expecting the line to
 * vanish from the thread.
 *
 * Confirming closes nothing on its own: `AlertDialogAction` is a plain Button
 * where `AlertDialogCancel` wraps a Close, so the caller shuts it in
 * `onConfirm` — as every other dialog of the application does.
 */
export function DeleteUpdateDialog({
  open,
  onOpenChange,
  onConfirm,
}: DeleteUpdateDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Supprimer cette mise à jour ?</AlertDialogTitle>
          <AlertDialogDescription>
            Son texte et les réactions qu&apos;elle a reçues seront perdus
            définitivement. Elle gardera sa place dans le fil, marquée « Message
            supprimé ».
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel className="cursor-pointer">Annuler</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="cursor-pointer bg-red-600 text-white hover:bg-red-700"
          >
            Supprimer
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
