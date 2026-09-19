"use client";

import { Search } from "lucide-react";
import { useState } from "react";

import { useComboboxFilter } from "@/components/ui/combobox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useProjects } from "@/lib/api/queries";

interface AttachMissionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The mission being attached: it is never offered as its own project. */
  missionId: number;
  label: string;
  /** Work packages it already carries: what a refusal argues from. */
  subProjects: number;
  /** Whether the catalogue publishes it, which attaching would take away. */
  published: boolean;
  /** The project it already belongs to, when it is being moved. */
  currentParentId?: number | null;
  onConfirm: (parentId: number) => void | Promise<void>;
}

/**
 * Why the mission cannot become a slice of a project, and what to do first.
 *
 * Each obstacle carries its own way out, because they are not the same way: a
 * mission carrying packages must be emptied, since the list reads two levels
 * and not three; a published one must be unpublished, since its card would
 * leave waat.tools without anyone saying so.
 */
function refusal(label: string, subProjects: number, published: boolean): string {
  const said: string[] = [];
  if (subProjects > 0) {
    said.push(
      subProjects > 1
        ? `« ${label} » porte ${subProjects} sous-projets, et l'arborescence s'arrête à deux niveaux. Détachez-les d'abord.`
        : `« ${label} » porte un sous-projet, et l'arborescence s'arrête à deux niveaux. Détachez-le d'abord.`,
    );
  }
  if (published) {
    said.push(
      `« ${label} » est publiée au catalogue : le catalogue ne dessine qu'une fiche par service, et un sous-projet se publie à travers son projet. Dépubliez-la d'abord, depuis l'onglet Fiche service.`,
    );
  }
  return said.join(" ");
}

/**
 * The single door to attaching a mission — open in both cases.
 *
 * Whether it opens on a refusal or on a list of projects, the click that gets
 * here is the same: one asks where the mission belongs, and the dialog
 * answers. Hiding the action on a mission that cannot move would leave the
 * refusal unexplained, and there is something to say.
 *
 * Mounted only while it is open: it asks for the reference list, and no sheet
 * one merely reads has to pay for a list nobody is looking at.
 */
export function AttachMissionDialog({
  open,
  onOpenChange,
  missionId,
  label,
  subProjects,
  published,
  currentParentId = null,
  onConfirm,
}: AttachMissionDialogProps) {
  const { missions } = useProjects();
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const { contains } = useComboboxFilter();

  const attachable = subProjects === 0 && !published;

  // Only a project may carry a package: the hierarchy stops at two levels, and
  // off-project work produces nothing to slice. The project it already belongs
  // to is left out — choosing it would change nothing.
  const offered = missions
    .map((listed) => listed.project)
    .filter(
      (project) =>
        project.kind === "project" &&
        project.id !== missionId &&
        project.id !== currentParentId &&
        contains(project.label, search),
    );

  async function attachTo(parentId: number) {
    setBusy(true);
    try {
      await onConfirm(parentId);
      onOpenChange(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* Wider than a dialog that only asks a question: this one is read as a
          list, and the reference list's names are long. */}
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {attachable
              ? `Rattacher « ${label} » à un projet`
              : "Rattachement impossible"}
          </DialogTitle>
          <DialogDescription>
            {attachable
              ? "Elle en devient un sous-projet. Sa phase, son estimé et les jours déjà saisis restent sur elle : le projet en lit la somme. Elle prend en revanche l'axe stratégique du projet, à la place du sien."
              : refusal(label, subProjects, published)}
          </DialogDescription>
        </DialogHeader>

        {attachable && (
          // `min-w-0`, without which nothing below truncates: the dialog lays
          // its parts out in a grid, and a grid cell is free to grow to the
          // width of what it holds. The longest name would stretch it, the
          // buttons would measure themselves against that stretched width, and
          // the list would run out of the dialog and over the page behind.
          <div className="min-w-0">
            <div className="flex items-center gap-2 border-b border-slate-200 px-1 pb-2">
              <Search className="size-4 shrink-0 text-slate-400" aria-hidden />
              <input
                type="text"
                autoFocus
                value={search}
                placeholder="Rechercher un projet…"
                aria-label="Rechercher un projet"
                onChange={(event) => setSearch(event.target.value)}
                className="min-w-0 flex-1 bg-transparent py-0.5 text-sm focus:outline-none"
              />
            </div>

            {offered.length === 0 ? (
              <p className="px-2 py-6 text-center text-sm text-slate-400">
                Aucun projet ne correspond.
              </p>
            ) : (
              <ul className="max-h-72 overflow-y-auto pt-1">
                {offered.map((project) => (
                  <li key={project.id}>
                    <button
                      type="button"
                      disabled={busy}
                      // Truncated, the name still reads in full on hover: the
                      // reference list holds labels no dialog is wide enough
                      // for, and one chooses a project by its whole name.
                      title={project.label}
                      onClick={() => void attachTo(project.id)}
                      className="w-full cursor-pointer truncate rounded px-2 py-2 text-left text-sm transition-colors hover:bg-slate-100 disabled:cursor-default disabled:opacity-50"
                    >
                      {project.label}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
