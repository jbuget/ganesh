"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";

import type { ProjectResponse } from "@/lib/api/generated/model";
import { libellePhase, pastillePhase } from "@/lib/board";

interface ProjectSubProjectsProps {
  sousProjets: ProjectResponse[];
}

/**
 * Les lots rattaches a une mission.
 *
 * Chaque ligne mene a la fiche du lot plutot que de la deplier ici : un lot se
 * pilote comme une mission a part entiere, avec ses propres intervenants et sa
 * propre consommation, et n'a pas sa place en resume dans la fiche du parent.
 */
export function ProjectSubProjects({ sousProjets }: ProjectSubProjectsProps) {
  if (sousProjets.length === 0) {
    return <p className="text-sm text-slate-400">Aucun sous-projet</p>;
  }

  return (
    <ul className="space-y-0.5">
      {sousProjets.map((lot) => (
        <li key={lot.id}>
          <Link
            href={`/projets/${lot.id}`}
            className="group flex cursor-pointer items-center gap-2 rounded px-1 py-1.5 transition-colors hover:bg-slate-50"
          >
            {lot.statut && (
              <span
                aria-hidden
                className={`size-2.5 shrink-0 rounded-full ${pastillePhase(lot.statut)}`}
              />
            )}
            <span className="min-w-0 flex-1 truncate text-sm text-slate-700">
              {lot.label}
            </span>
            {lot.statut && (
              <span className="shrink-0 text-xs text-slate-500">
                {libellePhase(lot.statut)}
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
