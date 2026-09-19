"use client";

import { HORIZONS } from "@/lib/planning";

interface HorizonSelectProps {
  months: number;
  onChange: (months: number) => void;
}

/**
 * How far ahead the plan looks.
 *
 * Three choices laid side by side rather than folded into a menu: the horizon
 * is changed while reading, to see whether something that does not fit in six
 * months fits in twelve, and a menu would cost a click each time.
 */
export function HorizonSelect({ months, onChange }: HorizonSelectProps) {
  return (
    <div
      role="group"
      aria-label="Horizon de projection"
      className="flex items-center rounded-md border border-slate-300 bg-white p-0.5"
    >
      {HORIZONS.map((horizon) => {
        const isChosen = horizon.months === months;
        return (
          <button
            key={horizon.months}
            type="button"
            aria-pressed={isChosen}
            onClick={() => onChange(horizon.months)}
            className={[
              "cursor-pointer rounded px-2.5 py-1 text-sm transition-colors",
              isChosen
                ? "bg-slate-100 font-medium text-slate-900"
                : "text-slate-600 hover:text-slate-900",
            ].join(" ")}
          >
            {horizon.label}
          </button>
        );
      })}
    </div>
  );
}
