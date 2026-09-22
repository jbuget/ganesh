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
import type { ProjectKind } from "@/lib/api/generated/model";
import { useProjects } from "@/lib/api/queries";

interface ConvertRequestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (kind: ProjectKind, parentId: number | null) => Promise<void>;
}

/**
 * Making a mission of an accepted need.
 *
 * The only thing still to be told: whether it stands on its own or becomes a
 * work package of a mission already under way. Everything else crosses over
 * from the need — the title, the departments, what it describes — and what
 * the team declares, the axis and the urgency, is declared on the project
 * afterwards by whoever will carry it.
 *
 * Mounted only while it is open: it asks for the reference list, and no panel
 * one merely reads has to pay for a list nobody is looking at.
 */
export function ConvertRequestDialog({
  open,
  onOpenChange,
  onConfirm,
}: ConvertRequestDialogProps) {
  const { missions } = useProjects();
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const { contains } = useComboboxFilter();

  // Only a project may carry a package: the hierarchy stops at two levels,
  // and off-project work produces nothing to slice.
  const offered = missions
    .map((listed) => listed.project)
    .filter((project) => project.kind === "project" && contains(project.label, search));

  async function convert(kind: ProjectKind, parentId: number | null) {
    setBusy(true);
    try {
      await onConfirm(kind, parentId);
      setSearch("");
      onOpenChange(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) setSearch("");
        onOpenChange(next);
      }}
    >
      {/* Wider than a dialog that only asks a question: this one is read as a
          list, and the reference list's names are long. */}
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Convertir en projet</DialogTitle>
          <DialogDescription>
            Le projet reprend l&apos;intitulé, les départements et ce que la demande
            décrit. Sa phase repart à Exploration ; l&apos;axe et la priorité restent à
            déclarer.
          </DialogDescription>
        </DialogHeader>

        <div className="min-w-0">
          <button
            type="button"
            disabled={busy}
            onClick={() => void convert("project", null)}
            className="mb-2 w-full cursor-pointer rounded border border-slate-300 px-3 py-2 text-left text-sm font-medium transition-colors hover:bg-slate-50"
          >
            Créer un projet à part entière
          </button>

          <p className="px-1 pb-1 text-xs text-slate-500">
            …ou en faire un sous-projet d&apos;un projet existant :
          </p>

          <div className="flex items-center gap-2 border-b border-slate-200 px-1 pb-2">
            <Search className="size-4 shrink-0 text-slate-400" aria-hidden />
            <input
              type="text"
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
            <ul className="max-h-64 overflow-y-auto pt-1">
              {offered.map((project) => (
                <li key={project.id}>
                  <button
                    type="button"
                    disabled={busy}
                    title={project.label}
                    onClick={() => void convert("work_package", project.id)}
                    className="w-full cursor-pointer truncate rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                  >
                    {project.label}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
