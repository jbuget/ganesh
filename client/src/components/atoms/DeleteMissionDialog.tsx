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
  /** Whether the catalogue draws a card for it. */
  published: boolean;
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
 *
 * The publication is said last, and only on its own: archiving answers the
 * time in full — the catalogue keeps the card and marks it archived — so
 * sending one to unpublish first would add a step that changes nothing.
 */
function refusal({
  label,
  consumedDays,
  subProjects,
  published,
}: Pick<
  DeleteMissionDialogProps,
  "label" | "consumedDays" | "subProjects" | "published"
>): string {
  const said: string[] = [];
  if (consumedDays > 0) {
    const days = consumedDays >= 2 ? "jours saisis" : "jour saisi";
    said.push(
      `« ${label} » porte ${formatDecimalDays(consumedDays)} ${days} : le supprimer effacerait du temps déclaré. Archivez-le plutôt, il sort des listes sans que rien ne soit perdu.`,
    );
  }
  if (subProjects > 0) {
    said.push(
      subProjects > 1
        ? `« ${label} » porte ${subProjects} sous-projets, qui peuvent eux-mêmes porter du temps. Traitez-les d'abord : la suppression ne descend pas dans l'arborescence.`
        : `« ${label} » porte un sous-projet, qui peut lui-même porter du temps. Traitez-le d'abord : la suppression ne descend pas dans l'arborescence.`,
    );
  }
  if (published && said.length === 0) {
    said.push(
      `« ${label} » est publié au catalogue : sa carte quitterait waat.tools sans que personne ne l'ait décidé. Dépubliez-le d'abord, depuis l'onglet « Catalogue ».`,
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
  published,
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
              ? "Ce projet n'a jamais porté de temps. Sa suppression est définitive : elle emporte le fil de ses mises à jour, les fichiers qui y ont été déposés, ses contributeurs et ses dates de passage de phase. Rien ne permettra de le rétablir."
              : refusal({ label, consumedDays, subProjects, published })}
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
              Supprimer le projet
            </AlertDialogAction>
          )}
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
