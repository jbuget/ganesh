"use client";

import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export interface FilterOption {
  value: string;
  label: string;
  /** Dot or thumbnail shown before the label, if there is one. */
  thumbnail?: React.ReactNode;
}

interface FilterSelectProps {
  label: string;
  options: FilterOption[];
  values: string[];
  onChange: (values: string[]) => void;
}

/**
 * A filter criterion with multiple choices.
 *
 * Each value toggles on click, with no confirmation and no closing: three get
 * ticked in a row without reopening the menu. The trigger announces how many
 * are kept, so the bar says what it filters once folded.
 */
export function FilterSelect({ label, options, values, onChange }: FilterSelectProps) {
  const [isOpen, setOuvert] = useState(false);
  const chosen = new Set(values);

  function toggle(value: string) {
    const next_ones = new Set(chosen);
    if (next_ones.has(value)) next_ones.delete(value);
    else next_ones.add(value);
    // The order of the options is what counts: two identical selections
    // produce the same address, whatever the order of the clicks.
    onChange(options.filter((o) => next_ones.has(o.value)).map((o) => o.value));
  }

  return (
    <Popover open={isOpen} onOpenChange={setOuvert}>
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
