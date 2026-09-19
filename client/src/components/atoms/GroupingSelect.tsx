"use client";

import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { GROUPINGS, groupingLabel, type Grouping } from "@/lib/roadmap";

interface GroupingSelectProps {
  value: Grouping;
  onChange: (value: Grouping) => void;
}

//: Wide enough for the longest grouping on offer, and fixed: a control that
//: resized with its label would make the header jump on every change.
const WIDTH = "w-52";

/**
 * How the lines are gathered into bands.
 *
 * The real setting of this screen: the grouping decides who the roadmap is
 * being shown to. A steering committee reads axes, a phase review reads
 * phases, and the same drawing serves both.
 */
export function GroupingSelect({ value, onChange }: GroupingSelectProps) {
  const [isOpen, setOpen] = useState(false);

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={`Regroupement, actuellement ${groupingLabel(value)}`}
        className={`flex ${WIDTH} cursor-pointer items-center justify-between gap-1.5 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-700 transition-colors hover:border-slate-400`}
      >
        <span className="truncate">{groupingLabel(value)}</span>
        <ChevronDown className="size-3.5 shrink-0 opacity-60" aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="end" className={`${WIDTH} p-1`}>
        <ul role="listbox" aria-label="Regroupement des missions">
          {GROUPINGS.map((grouping) => {
            const isChosen = grouping.value === value;
            return (
              <li key={grouping.value} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={isChosen}
                  onClick={() => {
                    setOpen(false);
                    if (!isChosen) onChange(grouping.value);
                  }}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  <span className="min-w-0 flex-1 truncate">{grouping.label}</span>
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
