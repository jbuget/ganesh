"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Department } from "@/lib/api/generated/model";
import { DEPARTEMENTS, departmentLabel } from "@/lib/departments";

interface DepartmentPickerProps {
  values: Department[];
  onChange: (values: Department[]) => void | Promise<void>;
}

/**
 * Departments a mission concerns.
 *
 * Several are possible: a tool serving landlords and customer service concerns
 * both, and steering wants to see it on both sides.
 */
export function DepartmentPicker({ values, onChange }: DepartmentPickerProps) {
  const [isOpen, setOuvert] = useState(false);
  const chosen = new Set(values);

  function toggle(value: Department) {
    const next_ones = new Set(chosen);
    if (next_ones.has(value)) next_ones.delete(value);
    else next_ones.add(value);
    void onChange(
      DEPARTEMENTS.filter((d) => next_ones.has(d.value)).map((d) => d.value),
    );
  }

  return (
    <Popover open={isOpen} onOpenChange={setOuvert}>
      <PopoverTrigger
        aria-label="Modifier les départements"
        className="-mx-1 flex cursor-pointer flex-wrap items-center gap-1 rounded px-1 py-0.5 transition-colors hover:bg-slate-100"
      >
        {values.length === 0 ? (
          <span className="flex items-center gap-1 text-sm text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            Départements
          </span>
        ) : (
          values.map((value) => (
            <span
              key={value}
              className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-700"
            >
              {departmentLabel(value)}
            </span>
          ))
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-64 p-1">
        <ul>
          {DEPARTEMENTS.map((departement) => {
            const present = chosen.has(departement.value);
            return (
              <li key={departement.value}>
                <button
                  type="button"
                  aria-pressed={present}
                  onClick={() => toggle(departement.value)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  <span className="min-w-0 flex-1 truncate">{departement.label}</span>
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
