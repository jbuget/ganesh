"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface Option<T extends string> {
  value: T;
  label: string;
}

interface OptionPickerProps<T extends string> {
  value: T | null | undefined;
  options: readonly Option<T>[];
  /** What the row asks for: the empty state and the accessible name. */
  label: string;
  onChange: (value: T | null) => void | Promise<void>;
}

/**
 * One value out of a closed list, or none.
 *
 * Picking the current value again removes it: it is the only way back to
 * « nothing chosen », and the sheet has no other place to say so.
 */
export function OptionPicker<T extends string>({
  value,
  options,
  label,
  onChange,
}: OptionPickerProps<T>) {
  const [isOpen, setOpen] = useState(false);
  const chosen = options.find((option) => option.value === value);

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={label}
        className="-mx-1 flex cursor-pointer items-center rounded px-1 py-0.5 transition-colors hover:bg-slate-100"
      >
        {chosen ? (
          <span className="text-sm text-slate-700">{chosen.label}</span>
        ) : (
          <span className="flex items-center gap-1 text-sm text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            {label}
          </span>
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-56 p-1">
        <ul>
          {options.map((option) => (
            <li key={option.value}>
              <button
                type="button"
                aria-pressed={option.value === value}
                onClick={() => {
                  setOpen(false);
                  void onChange(option.value === value ? null : option.value);
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <span className="min-w-0 flex-1 truncate">{option.label}</span>
                {option.value === value && (
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
