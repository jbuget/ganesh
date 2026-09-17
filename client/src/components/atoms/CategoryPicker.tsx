"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ProjectCategory } from "@/lib/api/generated/model";
import { CATEGORIES, categorie } from "@/lib/board";

interface CategoryPickerProps {
  valeur: ProjectCategory | null | undefined;
  onChange: (valeur: ProjectCategory | null) => void | Promise<void>;
}

/** Axe strategique d'une mission. Un seul, ou aucun. */
export function CategoryPicker({ valeur, onChange }: CategoryPickerProps) {
  const [ouvert, setOuvert] = useState(false);
  const axe = categorie(valeur);

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        aria-label="Changer la catégorie"
        className="-mx-1 flex cursor-pointer items-center rounded px-1 py-0.5 transition-colors hover:bg-slate-100"
      >
        {axe ? (
          <span className="flex items-center gap-1.5 text-sm text-slate-700">
            <span
              className={`size-2.5 shrink-0 rounded-[3px] ${axe.puce}`}
              aria-hidden
            />
            {axe.libelle}
          </span>
        ) : (
          <span className="flex items-center gap-1 text-sm text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            Catégorie
          </span>
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-64 p-1">
        <ul>
          {CATEGORIES.map((choix) => (
            <li key={choix.valeur}>
              <button
                type="button"
                aria-pressed={choix.valeur === valeur}
                onClick={() => {
                  setOuvert(false);
                  // Recliquer sur l'axe courant le retire : c'est le seul
                  // moyen de revenir a « aucune categorie ».
                  void onChange(choix.valeur === valeur ? null : choix.valeur);
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <span
                  className={`size-2.5 shrink-0 rounded-[3px] ${choix.puce}`}
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
