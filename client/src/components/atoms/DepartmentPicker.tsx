"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Department } from "@/lib/api/generated/model";
import { DEPARTEMENTS, libelleDepartement } from "@/lib/departments";

interface DepartmentPickerProps {
  valeurs: Department[];
  onChange: (valeurs: Department[]) => void | Promise<void>;
}

/**
 * Departements concernes par une mission.
 *
 * Plusieurs sont possibles : un outil qui sert les bailleurs et le service
 * client concerne les deux, et le pilotage veut le voir des deux cotes.
 */
export function DepartmentPicker({ valeurs, onChange }: DepartmentPickerProps) {
  const [ouvert, setOuvert] = useState(false);
  const choisis = new Set(valeurs);

  function basculer(valeur: Department) {
    const suivants = new Set(choisis);
    if (suivants.has(valeur)) suivants.delete(valeur);
    else suivants.add(valeur);
    void onChange(
      DEPARTEMENTS.filter((d) => suivants.has(d.valeur)).map((d) => d.valeur),
    );
  }

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        aria-label="Modifier les départements"
        className="-mx-1 flex cursor-pointer flex-wrap items-center gap-1 rounded px-1 py-0.5 transition-colors hover:bg-slate-100"
      >
        {valeurs.length === 0 ? (
          <span className="flex items-center gap-1 text-sm text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            Départements
          </span>
        ) : (
          valeurs.map((valeur) => (
            <span
              key={valeur}
              className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-700"
            >
              {libelleDepartement(valeur)}
            </span>
          ))
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-64 p-1">
        <ul>
          {DEPARTEMENTS.map((departement) => {
            const present = choisis.has(departement.valeur);
            return (
              <li key={departement.valeur}>
                <button
                  type="button"
                  aria-pressed={present}
                  onClick={() => basculer(departement.valeur)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  <span className="min-w-0 flex-1 truncate">{departement.libelle}</span>
                  {present && (
                    <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
