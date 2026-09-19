"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface YearSelectProps {
  year: number;
  onChange: (year: number) => void;
}

/**
 * The year the roadmap is read over.
 *
 * A year and not a sliding horizon: « et cette année, on livre quoi ? » is
 * the question a roadmap is opened for, and a window that moved with the
 * calendar would make two readings of it impossible to compare.
 */
export function YearSelect({ year, onChange }: YearSelectProps) {
  return (
    <div
      role="group"
      aria-label="Année lue"
      className="flex items-center gap-1 rounded-md border border-slate-300 bg-white px-1 py-0.5"
    >
      <button
        type="button"
        aria-label="Année précédente"
        onClick={() => onChange(year - 1)}
        className="cursor-pointer rounded p-1 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
      >
        <ChevronLeft className="size-4" aria-hidden />
      </button>

      <span className="px-1 text-sm font-medium text-slate-800 tabular-nums">
        {year}
      </span>

      <button
        type="button"
        aria-label="Année suivante"
        onClick={() => onChange(year + 1)}
        className="cursor-pointer rounded p-1 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
      >
        <ChevronRight className="size-4" aria-hidden />
      </button>
    </div>
  );
}
