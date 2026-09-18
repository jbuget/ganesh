"use client";

import { Check } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ProjectStatus } from "@/lib/api/generated/model";
import { PHASES, phaseLabel, phaseDot } from "@/lib/board";

interface PhasePickerProps {
  status: ProjectStatus | null;
  onChange: (status: ProjectStatus) => void | Promise<void>;
}

/**
 * A mission's phase, changeable from its sheet.
 *
 * The kanban already moves a mission along by dragging it; from the sheet, one
 * corrects it without having to find its card again.
 */
export function PhasePicker({ status, onChange }: PhasePickerProps) {
  const [isOpen, setOpen] = useState(false);

  if (status === null) {
    return <span className="text-sm text-slate-400">Hors projet</span>;
  }

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label="Changer la phase"
        className="-mx-1 flex cursor-pointer items-center gap-1.5 rounded px-1 py-0.5 text-sm text-slate-700 transition-colors hover:bg-slate-100"
      >
        <span aria-hidden className={`size-2.5 rounded-full ${phaseDot(status)}`} />
        {phaseLabel(status)}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-52 p-1">
        <ul>
          {PHASES.map((phase) => (
            <li key={phase.status}>
              <button
                type="button"
                aria-pressed={phase.status === status}
                onClick={() => {
                  setOpen(false);
                  if (phase.status !== status) void onChange(phase.status);
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <span
                  aria-hidden
                  className={`size-2.5 shrink-0 rounded-full ${phase.dot}`}
                />
                <span className="min-w-0 flex-1 truncate">{phase.label}</span>
                {phase.status === status && (
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
