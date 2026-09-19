"use client";

import { ChevronRight, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ProjectResponse } from "@/lib/api/generated/model";
import { phaseLabel, phaseDot } from "@/lib/board";

interface ProjectSubProjectsProps {
  subProjects: ProjectResponse[];
  /** A name is all it takes: the rest is steered from the package's own sheet. */
  onAdd: (label: string) => Promise<void>;
}

/**
 * The work packages attached to a mission.
 *
 * Each row leads to the package's sheet rather than unfolding it here: a work
 * package is steered like a mission in its own right, with its own contributors
 * and its own consumption, and has no place summarised in the parent's sheet.
 *
 * Adding one stays on the parent: at scoping a project is cut into three or
 * four packages in a row, and being taken into each one as it is created would
 * mean coming back three or four times.
 */
export function ProjectSubProjects({ subProjects, onAdd }: ProjectSubProjectsProps) {
  const [isOpen, setOpen] = useState(false);
  const [label, setLabel] = useState("");
  const [busy, setBusy] = useState(false);

  const isValid = label.trim().length > 0;

  function toggleExpanded(value: boolean) {
    setOpen(value);
    // Closing, in any way at all, resets the field.
    if (!value) setLabel("");
  }

  async function add() {
    if (!isValid) return;
    setBusy(true);
    try {
      await onAdd(label.trim());
      toggleExpanded(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-1">
      {subProjects.length === 0 ? (
        <p className="text-sm text-slate-400">Aucun sous-projet</p>
      ) : (
        <ul className="space-y-0.5">
          {subProjects.map((workPackage) => (
            <li key={workPackage.id}>
              <Link
                href={`/projects/${workPackage.id}`}
                className="group flex cursor-pointer items-center gap-2 rounded px-1 py-1.5 transition-colors hover:bg-slate-50"
              >
                {workPackage.status && (
                  <span
                    aria-hidden
                    className={`size-2.5 shrink-0 rounded-full ${phaseDot(workPackage.status)}`}
                  />
                )}
                <span className="min-w-0 flex-1 truncate text-sm text-slate-700">
                  {workPackage.label}
                </span>
                {workPackage.status && (
                  <span className="shrink-0 text-xs text-slate-500">
                    {phaseLabel(workPackage.status)}
                  </span>
                )}
                <ChevronRight
                  aria-hidden
                  className="size-4 shrink-0 text-slate-300 opacity-0 transition-opacity group-hover:opacity-100"
                />
              </Link>
            </li>
          ))}
        </ul>
      )}

      {/* A popover rather than a dialog, like the other fields of the sheet:
          the panel must not vanish behind a veil for a single name. */}
      <Popover open={isOpen} onOpenChange={toggleExpanded}>
        <PopoverTrigger className="flex cursor-pointer items-center gap-1 px-1 text-sm text-slate-400 transition-colors hover:text-slate-600">
          <Plus className="size-3.5" aria-hidden />
          Ajouter un sous-projet
        </PopoverTrigger>

        <PopoverContent align="start" className="w-80 gap-1.5">
          <Input
            value={label}
            autoFocus
            aria-label="Nom du sous-projet"
            placeholder="Reprise de données"
            className="h-8 text-sm"
            onChange={(event) => setLabel(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void add();
            }}
          />
          <div className="flex gap-2">
            <Button size="sm" disabled={!isValid || busy} onClick={() => void add()}>
              Ajouter
            </Button>
            <Button size="sm" variant="ghost" onClick={() => toggleExpanded(false)}>
              Annuler
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
