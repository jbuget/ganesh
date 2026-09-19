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

interface DeleteMissionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  label: string;
  /** Whether the mission never served, and may therefore disappear. */
  deletable: boolean;
  /** Days already declared on it. */
  consumedDays: number;
  /** Work packages attached to it. */
  subProjects: number;
  onConfirm: () => void | Promise<void>;
}

/**
 * Why the deletion is refused, and what to do instead.
 *
 * Each obstacle carries its own way out, because they are not the same way:
 * time declared calls for archiving, which keeps it; a work package calls for
 * dealing with the package first, since the deletion does not go down the
 * tree — and archiving the project would not take it away either. Saying « il
 * y a du temps » on a project whose own count is zero, because a package
 * under it carries some, would send one looking for entries that are not
 * there.
 */
function refusal(label: string, consumedDays: number, subProjects: number): string {
  const said: string[] = [];
  if (consumedDays > 0) {
    const days = consumedDays >= 2 ? "jours saisis" : "jour saisi";
    said.push(
      `« ${label} » porte ${formatDecimalDays(consumedDays)} ${days} : la supprimer effacerait du temps déclaré. Archivez-la plutôt, elle sort des listes sans que rien ne soit perdu.`,
    );
  }
  if (subProjects > 0) {
    said.push(
      subProjects > 1
        ? `« ${label} » porte ${subProjects} sous-projets, qui peuvent eux-mêmes porter du temps. Traitez-les d'abord : la suppression ne descend pas dans l'arborescence.`
        : `« ${label} » porte un sous-projet, qui peut lui-même porter du temps. Traitez-le d'abord : la suppression ne descend pas dans l'arborescence.`,
    );
  }
  return said.join(" ");
}

/**
 * The single door to deleting a mission — open in both cases.
 *
 * Whether it opens on a refusal or on a confirmation, the click that gets here
 * is the same: one asks to delete, and the dialog answers. Hiding the action
 * on a used mission would leave the refusal unexplained, and there is
 * something to say — the time it carries, and that archiving keeps it.
 */
export function DeleteMissionDialog({
  open,
  onOpenChange,
  label,
  deletable,
  consumedDays,
  subProjects,
  onConfirm,
}: DeleteMissionDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {deletable ? `Supprimer « ${label} » ?` : "Suppression impossible"}
          </AlertDialogTitle>
          <AlertDialogDescription>
            {deletable
              ? "Cette mission n'a jamais porté de temps. Sa suppression est définitive, et emporte les mises à jour publiées sur son fil : rien ne permettra de la rétablir."
              : refusal(label, consumedDays, subProjects)}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel className="cursor-pointer">
            {deletable ? "Annuler" : "Fermer"}
          </AlertDialogCancel>
          {deletable && (
            <AlertDialogAction
              onClick={onConfirm}
              className="cursor-pointer bg-red-600 text-white hover:bg-red-700"
            >
              Supprimer la mission
            </AlertDialogAction>
          )}
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
