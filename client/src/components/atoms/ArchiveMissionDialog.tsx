"use client";

import { Archive, CornerLeftUp } from "lucide-react";

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import type { SubProjectPolicy } from "@/lib/api/generated/model";

interface ArchiveMissionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  label: string;
  /** Work packages still in the reference list under the mission. */
  subProjects: number;
  onConfirm: (policy: SubProjectPolicy) => void | Promise<void>;
}

/**
 * What becomes of a project's slices when the project leaves.
 *
 * The dialog only opens where the question arises: a mission carrying no
 * package is archived on the spot, without a word. Where it does arise, the
 * two answers are not offered as equals — leaving them behind, steered on
 * behalf of a project that has gone, is exactly what this asks about, and
 * « Annuler » is the third way out for whoever wants to deal with a package
 * by hand first.
 */
export function ArchiveMissionDialog({
  open,
  onOpenChange,
  label,
  subProjects,
  onConfirm,
}: ArchiveMissionDialogProps) {
  const many = subProjects > 1;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {`« ${label} » porte ${many ? `${subProjects} sous-projets` : "un sous-projet"}.`}
          </AlertDialogTitle>
          <AlertDialogDescription>
            {`L'archivage ne descend pas dans l'arborescence : dites ce ${many ? "qu'ils deviennent" : "qu'il devient"}.`}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {/* Each answer says what it costs on its own line: one reads the
            consequence, not only the verb. */}
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => void onConfirm("archive")}
            className="flex cursor-pointer items-start gap-3 rounded border border-slate-200 p-3 text-left transition-colors hover:bg-slate-50"
          >
            <Archive className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden />
            <span className="min-w-0">
              <span className="block text-sm font-medium text-slate-900">
                {many
                  ? `Archiver aussi les ${subProjects} sous-projets`
                  : "Archiver aussi le sous-projet"}
              </span>
              <span className="block text-sm text-slate-500">
                {many
                  ? "Ils sortent des écrans avec le projet, et restent rattachés à lui : ce qu'il a coûté reste lisible."
                  : "Il sort des écrans avec le projet, et lui reste rattaché : ce que le projet a coûté reste lisible."}
              </span>
            </span>
          </button>

          <button
            type="button"
            onClick={() => void onConfirm("detach")}
            className="flex cursor-pointer items-start gap-3 rounded border border-slate-200 p-3 text-left transition-colors hover:bg-slate-50"
          >
            <CornerLeftUp
              className="mt-0.5 size-4 shrink-0 text-slate-400"
              aria-hidden
            />
            <span className="min-w-0">
              <span className="block text-sm font-medium text-slate-900">
                {many
                  ? "Les détacher en projets autonomes"
                  : "Le détacher en projet autonome"}
              </span>
              <span className="block text-sm text-slate-500">
                {many
                  ? "Ils restent pilotés et gardent l'axe qu'ils lisaient, mais le projet archivé ne comptera plus leurs jours."
                  : "Il reste piloté et garde l'axe qu'il lisait, mais le projet archivé ne comptera plus ses jours."}
              </span>
            </span>
          </button>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel className="cursor-pointer">Annuler</AlertDialogCancel>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
