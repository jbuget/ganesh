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
 * Confirmation avant de couper l'acces d'un utilisateur.
 *
 * Rien n'est efface : les saisies passees restent et continuent d'alimenter les
 * totaux par projet. Le dire ici evite d'hesiter devant une action reversible.
 *
 * Le retablissement, lui, ne passe pas par une confirmation : il ne retire rien
 * a personne.
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
            entries passées sont conservées. Un manager peut le réactiver à tout moment.
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
