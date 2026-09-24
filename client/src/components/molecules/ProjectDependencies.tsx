"use client";

import { Check, Plus, Search, X } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useComboboxFilter } from "@/components/ui/combobox";
import type { MissionRefResponse } from "@/lib/api/generated/model";
import { useProjects } from "@/lib/api/queries";

interface ProjectDependenciesProps {
  projectId: number;
  dependencies: MissionRefResponse[];
  /**
   * Whether the reader may change it.
   *
   * Editable by default: a field one cannot change is the exception, and it
   * is the screen holding the field that knows — a guest reads every sheet of
   * the reference list and rewrites none.
   */
  editable?: boolean;
  onChange: (dependsOn: number[]) => void | Promise<void>;
}

/**
 * The internal services a mission relies on.
 *
 * Only projects and work packages are offered: off-project work produces no
 * service, and a mission never depends on itself. Each name toggles on the
 * next click, with no confirmation and no closing — a dependency graph is
 * drawn in one sitting.
 */
export function ProjectDependencies({
  projectId,
  dependencies,
  editable = true,
  onChange,
}: ProjectDependenciesProps) {
  const { missions } = useProjects();
  const [isOpen, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { contains } = useComboboxFilter();

  const chosen = dependencies.map((dependency) => dependency.id);
  const offered = missions
    .map((listed) => listed.project)
    .filter(
      (mission) =>
        mission.id !== projectId &&
        mission.kind !== "off_project" &&
        contains(mission.label, search),
    );

  function toggle(otherId: number) {
    void onChange(
      chosen.includes(otherId)
        ? chosen.filter((kept) => kept !== otherId)
        : [...chosen, otherId],
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {dependencies.map((dependency) => (
        <span
          key={dependency.id}
          className="flex items-center gap-1 rounded border border-slate-200 bg-white py-0.5 pr-1 pl-2 text-sm text-slate-700"
        >
          {dependency.label}
          {editable && (
            <button
              type="button"
              aria-label={`Retirer ${dependency.label}`}
              onClick={() => toggle(dependency.id)}
              className="cursor-pointer rounded p-0.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
            >
              <X className="size-3" aria-hidden />
            </button>
          )}
        </span>
      ))}

      {editable && (
        <Popover open={isOpen} onOpenChange={setOpen}>
          <PopoverTrigger
            aria-label="Dépendances"
            className="flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 text-sm text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <Plus className="size-3.5" aria-hidden />
            {dependencies.length === 0 ? "Dépendances" : "Ajouter"}
          </PopoverTrigger>

          <PopoverContent align="start" className="w-72 p-1">
            <div className="flex items-center gap-2 border-b border-slate-200 px-2 pb-1.5">
              <Search className="size-3.5 shrink-0 text-slate-400" aria-hidden />
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
              <p className="px-2 py-3 text-center text-sm text-slate-400">
                Aucun projet ne correspond.
              </p>
            ) : (
              <ul className="max-h-64 overflow-y-auto pt-1">
                {offered.map((mission) => (
                  <li key={mission.id}>
                    <button
                      type="button"
                      aria-pressed={chosen.includes(mission.id)}
                      onClick={() => toggle(mission.id)}
                      className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                    >
                      <span className="min-w-0 flex-1 truncate">{mission.label}</span>
                      {chosen.includes(mission.id) && (
                        <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </PopoverContent>
        </Popover>
      )}
    </div>
  );
}
