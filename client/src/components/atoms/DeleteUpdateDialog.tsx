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
  /**
   * Whether what is being withdrawn is a reply rather than an update.
   *
   * The same gesture with the same consequences, so the same dialog: only
   * the two nouns move. Two dialogs saying the same thing would be two
   * chances to word the warning differently.
   */
  reply?: boolean;
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
  reply = false,
}: DeleteUpdateDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {reply ? "Supprimer cette réponse ?" : "Supprimer cette mise à jour ?"}
          </AlertDialogTitle>
          <AlertDialogDescription>
            Son texte et les réactions qu&apos;elle a reçues seront perdus
            définitivement. Elle gardera sa place dans{" "}
            {reply ? "la conversation" : "le fil"}, marquée « Message supprimé ».
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
