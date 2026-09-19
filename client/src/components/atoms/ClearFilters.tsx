"use client";

import { X } from "lucide-react";

interface ClearFiltersProps {
  onClear: () => void;
}

/**
 * Puts every criterion back to nothing, in one gesture.
 *
 * It is shown only once something is set: a screen that offers clearing what is
 * already empty makes the reader look for a filter they never applied.
 */
export function ClearFilters({ onClear }: ClearFiltersProps) {
  return (
    <button
      type="button"
      onClick={onClear}
      className="flex cursor-pointer items-center gap-1 rounded-md px-2 py-1.5 text-sm text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
    >
      <X className="size-3.5" aria-hidden />
      Effacer
    </button>
  );
}
