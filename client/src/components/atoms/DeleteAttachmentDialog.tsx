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
import { shownInUpdates } from "@/lib/attachments";

interface DeleteAttachmentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  filename: string;
  /** How many updates of the thread display the file. */
  usedInUpdates: number;
  onConfirm: () => void | Promise<void>;
}

/**
 * Confirming that a file goes — and saying what goes with it.
 *
 * A file shown in an update is not only a file: withdrawing it leaves a hole
 * in a thread somebody wrote. The count comes from the server, which is the
 * only side that can read the markdown of every update.
 */
export function DeleteAttachmentDialog({
  open,
  onOpenChange,
  filename,
  usedInUpdates,
  onConfirm,
}: DeleteAttachmentDialogProps) {
  const warning = shownInUpdates(usedInUpdates);

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Supprimer « {filename} » ?</AlertDialogTitle>
          <AlertDialogDescription>
            La suppression est définitive : le fichier ne pourra pas être rétabli.
            {warning ? ` ${warning}` : ""}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel className="cursor-pointer">Annuler</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="cursor-pointer bg-red-600 text-white hover:bg-red-700"
          >
            Supprimer le fichier
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
