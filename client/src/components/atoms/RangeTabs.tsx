"use client";

import type { PeriodRange } from "@/lib/api/generated/model";
import { RANGES } from "@/lib/statistics";

interface RangeTabsProps {
  value: PeriodRange;
  onChange: (range: PeriodRange) => void;
}

/**
 * The window being read, and the others on offer.
 *
 * Tabs rather than a dropdown: there are five of them, they never change, and
 * comparing two windows is a matter of one click back and forth.
 */
export function RangeTabs({ value, onChange }: RangeTabsProps) {
  return (
    <div role="tablist" aria-label="Plage de temps" className="flex gap-1">
      {RANGES.map((range) => {
        const isSelected = range.value === value;
        return (
          <button
            key={range.value}
            type="button"
            role="tab"
            aria-selected={isSelected}
            onClick={() => !isSelected && onChange(range.value)}
            className={[
              "cursor-pointer rounded-md px-3 py-1.5 text-sm transition-colors",
              isSelected
                ? "bg-slate-900 font-medium text-white"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
            ].join(" ")}
          >
            {range.label}
          </button>
        );
      })}
    </div>
  );
}
