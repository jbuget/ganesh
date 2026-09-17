"use client";

import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export interface FilterOption {
  value: string;
  label: string;
  /** Pastille ou vignette affichee devant le libelle, s'il y en a une. */
  thumbnail?: React.ReactNode;
}

interface FilterSelectProps {
  label: string;
  options: FilterOption[];
  values: string[];
  onChange: (values: string[]) => void;
}

/**
 * Un critere de filtrage a choix multiples.
 *
 * Chaque valeur bascule au clic, sans validation ni fermeture : on en coche
 * trois d'affilee sans rouvrir le menu. Le declencheur annonce combien sont
 * retenues, pour que la barre dise ce qu'elle filtre une fois repliee.
 */
export function FilterSelect({ label, options, values, onChange }: FilterSelectProps) {
  const [ouvert, setOuvert] = useState(false);
  const chosen = new Set(values);

  function toggle(value: string) {
    const next_ones = new Set(chosen);
    if (next_ones.has(value)) next_ones.delete(value);
    else next_ones.add(value);
    // L'ordre des options fait foi : deux selections identiques produisent la
    // meme adresse, quel que soit l'ordre des clics.
    onChange(options.filter((o) => next_ones.has(o.value)).map((o) => o.value));
  }

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        className={`flex cursor-pointer items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm transition-colors ${
          values.length > 0
            ? "border-sky-300 bg-sky-50 text-sky-900"
            : "border-slate-300 bg-white text-slate-700 hover:border-slate-400"
        }`}
      >
        {label}
        {values.length > 0 && (
          <span className="rounded-full bg-sky-600 px-1.5 text-xs font-medium tabular-nums text-white">
            {values.length}
          </span>
        )}
        <ChevronDown className="size-3.5 shrink-0 opacity-60" aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="start" className="w-60 p-1">
        <ul>
          {options.map((option) => {
            const kept = chosen.has(option.value);
            return (
              <li key={option.value}>
                <button
                  type="button"
                  aria-pressed={kept}
                  onClick={() => toggle(option.value)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  {option.thumbnail}
                  <span className="min-w-0 flex-1 truncate">{option.label}</span>
                  {kept && (
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
