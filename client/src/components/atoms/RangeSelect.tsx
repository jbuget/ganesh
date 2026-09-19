"use client";

import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { PeriodRange } from "@/lib/api/generated/model";
import { RANGES, rangeLabel } from "@/lib/statistics";

interface RangeSelectProps {
  value: PeriodRange;
  onChange: (range: PeriodRange) => void;
}

//: Wide enough for the longest window on offer. Fixed rather than fitted to
//: the label: a control that shrinks on « Hier » and grows on « 90 derniers
//: jours » makes the header jump every time the window changes.
const WIDTH = "w-44";

/**
 * The window the figures are read over.
 *
 * Folded into a menu rather than laid out in full: the header carries one
 * control, and the window in force is read at a glance instead of being
 * hunted for among five look-alike buttons.
 */
export function RangeSelect({ value, onChange }: RangeSelectProps) {
  const [isOpen, setOpen] = useState(false);

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={`Plage de temps, actuellement ${rangeLabel(value)}`}
        className={`flex ${WIDTH} cursor-pointer items-center justify-between gap-1.5 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-700 transition-colors hover:border-slate-400`}
      >
        <span className="truncate">{rangeLabel(value)}</span>
        <ChevronDown className="size-3.5 shrink-0 opacity-60" aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="end" className={`${WIDTH} p-1`}>
        <ul role="listbox" aria-label="Plage de temps">
          {RANGES.map((range) => {
            const isChosen = range.value === value;
            return (
              <li key={range.value} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={isChosen}
                  onClick={() => {
                    setOpen(false);
                    if (!isChosen) onChange(range.value);
                  }}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  <span className="min-w-0 flex-1 truncate">{range.label}</span>
                  {isChosen && (
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
