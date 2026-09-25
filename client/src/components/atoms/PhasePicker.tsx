"use client";

import { Check } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ProjectStatus } from "@/lib/api/generated/model";
import { PHASES, phaseLabel, phaseDot } from "@/lib/board";

interface PhasePickerProps {
  status: ProjectStatus | null;
  /**
   * Whether the reader may change it.
   *
   * Editable by default: a field one cannot change is the exception, and it
   * is the screen holding the field that knows — a guest reads every sheet of
   * the reference list and rewrites none.
   */
  editable?: boolean;
  onChange: (status: ProjectStatus) => void | Promise<void>;
}

/**
 * A mission's phase, changeable from its sheet.
 *
 * The kanban already moves a mission along by dragging it; from the sheet, one
 * corrects it without having to find its card again.
 */
export function PhasePicker({ status, editable = true, onChange }: PhasePickerProps) {
  const [isOpen, setOpen] = useState(false);

  if (status === null) {
    return <span className="text-sm text-slate-400">Hors projet</span>;
  }

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label="Changer la phase"
        disabled={!editable}
        className={`-mx-1 flex ${editable ? "cursor-pointer" : ""} items-center gap-1.5 rounded px-1 py-0.5 text-sm text-slate-700 transition-colors ${editable ? "hover:bg-slate-100" : ""}`}
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
