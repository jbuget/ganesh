"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ProjectPriority } from "@/lib/api/generated/model";
import { PRIORITES, priorite } from "@/lib/board";

interface PriorityPickerProps {
  valeur: ProjectPriority | null | undefined;
  onChange: (valeur: ProjectPriority | null) => void | Promise<void>;
}

/** Urgence d'une mission. Une seule, ou aucune. */
export function PriorityPicker({ valeur, onChange }: PriorityPickerProps) {
  const [ouvert, setOuvert] = useState(false);
  const urgence = priorite(valeur);

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        aria-label="Changer la priorité"
        className="-mx-1 flex cursor-pointer items-center rounded px-1 py-0.5 transition-colors hover:bg-slate-100"
      >
        {urgence ? (
          <span
            className={`rounded px-1.5 py-0.5 text-xs font-medium ${urgence.classe}`}
          >
            {urgence.libelle}
          </span>
        ) : (
          <span className="flex items-center gap-1 text-sm text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            Priorité
          </span>
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-48 p-1">
        <ul>
          {PRIORITES.map((choix) => (
            <li key={choix.valeur}>
              <button
                type="button"
                aria-pressed={choix.valeur === valeur}
                onClick={() => {
                  setOuvert(false);
                  // Recliquer sur l'urgence courante la retire : c'est le seul
                  // moyen de revenir a « aucune priorite ».
                  void onChange(choix.valeur === valeur ? null : choix.valeur);
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <span
                  className={`size-2.5 shrink-0 rounded-full ${choix.pastille}`}
                  aria-hidden
                />
                <span className="min-w-0 flex-1 truncate">{choix.libelle}</span>
                {choix.valeur === valeur && (
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
