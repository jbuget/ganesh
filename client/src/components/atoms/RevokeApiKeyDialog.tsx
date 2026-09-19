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

interface RevokeApiKeyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  name: string;
  onConfirm: () => void | Promise<void>;
}

/**
 * Confirmation before cutting a key.
 *
 * Unlike deactivating a teammate, this one does not come back: there is no
 * « unrevoke », and whatever was using the key stops on the next call. The
 * wording says both, because the gesture looks like every other red button.
 */
export function RevokeApiKeyDialog({
  open,
  onOpenChange,
  name,
  onConfirm,
}: RevokeApiKeyDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Révoquer « {name} » ?</AlertDialogTitle>
          <AlertDialogDescription>
            Tout ce qui utilise cette clé cessera de fonctionner dès le prochain appel.
            La révocation est immédiate et définitive : il faudra créer une nouvelle clé
            et la redéployer.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel className="cursor-pointer">Annuler</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="cursor-pointer bg-red-600 text-white hover:bg-red-700"
          >
            Révoquer
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
