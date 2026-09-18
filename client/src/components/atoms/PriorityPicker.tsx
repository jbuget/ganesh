"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ProjectPriority } from "@/lib/api/generated/model";
import { PRIORITIES, priority } from "@/lib/board";

interface PriorityPickerProps {
  value: ProjectPriority | null | undefined;
  onChange: (value: ProjectPriority | null) => void | Promise<void>;
}

/** A mission's urgency. One, or none. */
export function PriorityPicker({ value, onChange }: PriorityPickerProps) {
  const [ouvert, setOuvert] = useState(false);
  const urgency = priority(value);

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        aria-label="Changer la priorité"
        className="-mx-1 flex cursor-pointer items-center rounded px-1 py-0.5 transition-colors hover:bg-slate-100"
      >
        {urgency ? (
          <span className="flex items-center gap-1.5 text-sm text-slate-700">
            <urgency.icon className={`size-4 shrink-0 ${urgency.colour}`} aria-hidden />
            {urgency.label}
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
          {PRIORITIES.map((choice) => (
            <li key={choice.value}>
              <button
                type="button"
                aria-pressed={choice.value === value}
                onClick={() => {
                  setOuvert(false);
                  // Clicking the current urgency again removes it: the only
                  // way back to \u00ab no priority \u00bb.
                  void onChange(choice.value === value ? null : choice.value);
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <choice.icon
                  className={`size-4 shrink-0 ${choice.colour}`}
                  aria-hidden
                />
                <span className="min-w-0 flex-1 truncate">{choice.label}</span>
                {choice.value === value && (
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
