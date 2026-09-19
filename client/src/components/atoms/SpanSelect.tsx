"use client";

import { SPANS } from "@/lib/roadmap";

interface SpanSelectProps {
  months: number;
  onChange: (months: number) => void;
}

/**
 * How far ahead the roadmap looks.
 *
 * The control that decides how much the drawing is worth reading. Over a
 * year, a fortnight of work is a few pixels and every bar looks alike; over a
 * quarter, one sees a mission change phase. Three choices side by side rather
 * than folded into a menu: one flips between them while reading, and a menu
 * would cost a click each time.
 */
export function SpanSelect({ months, onChange }: SpanSelectProps) {
  return (
    <div
      role="group"
      aria-label="Fenêtre lue"
      className="flex items-center rounded-md border border-slate-300 bg-white p-0.5"
    >
      {SPANS.map((span) => {
        const isChosen = span.months === months;
        return (
          <button
            key={span.months}
            type="button"
            aria-pressed={isChosen}
            onClick={() => onChange(span.months)}
            className={[
              "cursor-pointer rounded px-2.5 py-1 text-sm transition-colors",
              isChosen
                ? "bg-slate-100 font-medium text-slate-900"
                : "text-slate-600 hover:text-slate-900",
            ].join(" ")}
          >
            {span.label}
          </button>
        );
      })}
    </div>
  );
}
