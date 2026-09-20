"use client";

import { Check, ChevronDown, Layers, Trash2 } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { SimulationResponse } from "@/lib/api/generated/model";
import { formatShortDate } from "@/lib/dates";
import { parisDay } from "@/lib/instants";

interface SimulationPickerProps {
  simulations: SimulationResponse[];
  /** The scenario currently open, if one is. */
  opened: SimulationResponse | null;
  onOpen: (simulation: SimulationResponse | null) => void;
  onDelete: (simulationId: number) => void;
}

/**
 * The scenarios the team keeps, to pick one from or to drop one.
 *
 * The first entry is the team's own plan, and it is an entry like the others:
 * coming back to what was actually decided must be as easy as opening a
 * hypothesis, or nobody will dare open one.
 */
export function SimulationPicker({
  simulations,
  opened,
  onOpen,
  onDelete,
}: SimulationPickerProps) {
  const [isOpen, setOpen] = useState(false);

  function choose(simulation: SimulationResponse | null) {
    onOpen(simulation);
    setOpen(false);
  }

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label="Choisir une simulation"
        className="flex cursor-pointer items-center gap-2 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-700 transition-colors hover:border-slate-400"
      >
        <Layers className="size-4 shrink-0 text-slate-400" aria-hidden />
        <span className="max-w-48 truncate">
          {opened ? opened.name : "Ordre de l'équipe"}
        </span>
        <ChevronDown className="size-4 shrink-0 text-slate-400" aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="start" className="w-72 p-1">
        <ul className="max-h-72 overflow-y-auto overscroll-contain">
          <li>
            <button
              type="button"
              aria-pressed={opened === null}
              onClick={() => choose(null)}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
            >
              <span className="min-w-0 flex-1 truncate text-slate-700">
                Ordre de l&apos;équipe
              </span>
              {opened === null && (
                <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
              )}
            </button>
          </li>

          {simulations.length > 0 && <li className="my-1 border-t border-border" />}

          {simulations.map((simulation) => {
            const isOpened = simulation.id === opened?.id;
            return (
              <li key={simulation.id} className="group flex items-center gap-1">
                <button
                  type="button"
                  aria-pressed={isOpened}
                  onClick={() => choose(simulation)}
                  className="flex min-w-0 flex-1 cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-slate-700">
                      {simulation.name}
                    </span>
                    <span className="block text-xs text-slate-400">
                      {formatShortDate(parisDay(simulation.updated_at))}
                    </span>
                  </span>
                  {isOpened && (
                    <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
                  )}
                </button>

                {/* Always present, never only on hover: a control one has to
                    go looking for is a control nobody finds. */}
                <button
                  type="button"
                  aria-label={`Supprimer la simulation ${simulation.name}`}
                  title={`Supprimer « ${simulation.name} »`}
                  onClick={() => onDelete(simulation.id)}
                  className="cursor-pointer rounded p-1.5 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
                >
                  <Trash2 className="size-4" aria-hidden />
                </button>
              </li>
            );
          })}
        </ul>

        {simulations.length === 0 && (
          <p className="px-2 py-4 text-center text-sm text-slate-400">
            Aucune simulation enregistrée.
          </p>
        )}
      </PopoverContent>
    </Popover>
  );
}
