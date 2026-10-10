"use client";

import { ChevronRight, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
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

      {/* The same gesture as the one folded in the mission menu, said with
          the same words and answered by the same dialog: two ways in, and
          nothing to tell apart once the name is asked for. */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex cursor-pointer items-center gap-1 px-1 text-sm text-slate-400 transition-colors hover:text-slate-600"
      >
        <Plus className="size-3.5" aria-hidden />
        Déclarer un sous-projet…
      </button>

      {isOpen && (
        <DeclareProjectDialog
          open
          kind="work_package"
          onOpenChange={setOpen}
          onConfirm={onAdd}
        />
      )}
    </div>
  );
}
