"use client";

import { Check } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ProjectStatus } from "@/lib/api/generated/model";
import { PHASES, libellePhase, pastillePhase } from "@/lib/board";

interface PhasePickerProps {
  statut: ProjectStatus | null;
  onChange: (statut: ProjectStatus) => void | Promise<void>;
}

/**
 * Phase d'une mission, changeable depuis sa fiche.
 *
 * Le kanban fait deja avancer une mission en la glissant ; depuis la fiche, on
 * la corrige sans avoir a retrouver sa carte.
 */
export function PhasePicker({ statut, onChange }: PhasePickerProps) {
  const [ouvert, setOuvert] = useState(false);

  if (statut === null) {
    return <span className="text-sm text-slate-400">Hors projet</span>;
  }

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        aria-label="Changer la phase"
        className="-mx-1 flex cursor-pointer items-center gap-1.5 rounded px-1 py-0.5 text-sm text-slate-700 transition-colors hover:bg-slate-100"
      >
        <span
          aria-hidden
          className={`size-2.5 rounded-full ${pastillePhase(statut)}`}
        />
        {libellePhase(statut)}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-52 p-1">
        <ul>
          {PHASES.map((phase) => (
            <li key={phase.statut}>
              <button
                type="button"
                aria-pressed={phase.statut === statut}
                onClick={() => {
                  setOuvert(false);
                  if (phase.statut !== statut) void onChange(phase.statut);
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <span
                  aria-hidden
                  className={`size-2.5 shrink-0 rounded-full ${phase.pastille}`}
                />
                <span className="min-w-0 flex-1 truncate">{phase.libelle}</span>
                {phase.statut === statut && (
                  <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
                )}
              </button>
            </li>
          ))}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
