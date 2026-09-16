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
import type { ProjectResponse } from "@/lib/api/generated/model";
import { useLastNonNull } from "@/lib/use-last-non-null";

interface DeleteProjectDialogProps {
  project: ProjectResponse | null;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => Promise<void>;
}

/** Confirmation avant suppression d'une mission jamais utilisee. */
export function DeleteProjectDialog({
  project,
  onOpenChange,
  onConfirm,
}: DeleteProjectDialogProps) {
  // Le nom doit rester lisible pendant l'animation de fermeture.
  const affiche = useLastNonNull(project);

  return (
    <AlertDialog open={project !== null} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Supprimer « {affiche?.label} » ?</AlertDialogTitle>
          <AlertDialogDescription>
            Cette mission ne porte aucune saisie : elle peut disparaître du référentiel.
            L&apos;opération est définitive.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel>Annuler</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}>Supprimer</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
