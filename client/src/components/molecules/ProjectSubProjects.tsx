"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";

import type { ProjectResponse } from "@/lib/api/generated/model";
import { phaseLabel, phaseDot } from "@/lib/board";

interface ProjectSubProjectsProps {
  subProjects: ProjectResponse[];
}

/**
 * The work packages attached to a mission.
 *
 * Each row leads to the package's sheet rather than unfolding it here: a work
 * package is steered like a mission in its own right, with its own contributors
 * and its own consumption, and has no place summarised in the parent's sheet.
 */
export function ProjectSubProjects({ subProjects }: ProjectSubProjectsProps) {
  if (subProjects.length === 0) {
    return <p className="text-sm text-slate-400">Aucun sous-projet</p>;
  }

  return (
    <ul className="space-y-0.5">
      {subProjects.map((lot) => (
        <li key={lot.id}>
          <Link
            href={`/projets/${lot.id}`}
            className="group flex cursor-pointer items-center gap-2 rounded px-1 py-1.5 transition-colors hover:bg-slate-50"
          >
            {lot.status && (
              <span
                aria-hidden
                className={`size-2.5 shrink-0 rounded-full ${phaseDot(lot.status)}`}
              />
            )}
            <span className="min-w-0 flex-1 truncate text-sm text-slate-700">
              {lot.label}
            </span>
            {lot.status && (
              <span className="shrink-0 text-xs text-slate-500">
                {phaseLabel(lot.status)}
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
  );
}
