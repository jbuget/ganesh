"use client";

import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export interface FilterOption {
  valeur: string;
  libelle: string;
  /** Pastille ou vignette affichee devant le libelle, s'il y en a une. */
  vignette?: React.ReactNode;
}

interface FilterSelectProps {
  libelle: string;
  options: FilterOption[];
  valeurs: string[];
  onChange: (valeurs: string[]) => void;
}

/**
 * Un critere de filtrage a choix multiples.
 *
 * Chaque valeur bascule au clic, sans validation ni fermeture : on en coche
 * trois d'affilee sans rouvrir le menu. Le declencheur annonce combien sont
 * retenues, pour que la barre dise ce qu'elle filtre une fois repliee.
 */
export function FilterSelect({
  libelle,
  options,
  valeurs,
  onChange,
}: FilterSelectProps) {
  const [ouvert, setOuvert] = useState(false);
  const choisies = new Set(valeurs);

  function basculer(valeur: string) {
    const suivantes = new Set(choisies);
    if (suivantes.has(valeur)) suivantes.delete(valeur);
    else suivantes.add(valeur);
    // L'ordre des options fait foi : deux selections identiques produisent la
    // meme adresse, quel que soit l'ordre des clics.
    onChange(options.filter((o) => suivantes.has(o.valeur)).map((o) => o.valeur));
  }

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        className={`flex cursor-pointer items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm transition-colors ${
          valeurs.length > 0
            ? "border-sky-300 bg-sky-50 text-sky-900"
            : "border-slate-300 bg-white text-slate-700 hover:border-slate-400"
        }`}
      >
        {libelle}
        {valeurs.length > 0 && (
          <span className="rounded-full bg-sky-600 px-1.5 text-xs font-medium tabular-nums text-white">
            {valeurs.length}
          </span>
        )}
        <ChevronDown className="size-3.5 shrink-0 opacity-60" aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="start" className="w-60 p-1">
        <ul>
          {options.map((option) => {
            const retenue = choisies.has(option.valeur);
            return (
              <li key={option.valeur}>
                <button
                  type="button"
                  aria-pressed={retenue}
                  onClick={() => basculer(option.valeur)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  {option.vignette}
                  <span className="min-w-0 flex-1 truncate">{option.libelle}</span>
                  {retenue && (
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
