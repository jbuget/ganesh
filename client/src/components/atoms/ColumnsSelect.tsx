"use client";

import { Check, ChevronDown, Columns3 } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  HIDEABLE_COLUMNS,
  type ColumnKey,
  type HiddenColumns,
} from "@/lib/mission-columns";

interface ColumnsSelectProps {
  hidden: HiddenColumns;
  onToggle: (column: ColumnKey) => void;
  onShowAll: () => void;
}

/**
 * What the reference list shows, column by column.
 *
 * A steering meeting opens on the whole panorama, then works on four columns:
 * the rest is read once and takes up room afterwards. Each one toggles on
 * click, with no confirmation and no closing — three go away in a row without
 * reopening the menu.
 *
 * It sits in the filter bar without borrowing its colours: a filter marked in
 * blue says the list is narrower than the board, and putting a column away
 * takes nothing off the list. The count says how many are missing, so the bar
 * still tells once folded.
 */
export function ColumnsSelect({ hidden, onToggle, onShowAll }: ColumnsSelectProps) {
  const [isOpen, setOpen] = useState(false);

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        className={`flex cursor-pointer items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm transition-colors ${
          hidden.size > 0
            ? "border-slate-400 bg-slate-100 text-slate-900"
            : "border-slate-300 bg-white text-slate-700 hover:border-slate-400"
        }`}
      >
        <Columns3 className="size-4 shrink-0 opacity-70" aria-hidden />
        Colonnes
        {hidden.size > 0 && (
          <span className="rounded-full bg-slate-600 px-1.5 text-xs font-medium tabular-nums text-white">
            {hidden.size}
          </span>
        )}
        <ChevronDown className="size-3.5 shrink-0 opacity-60" aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="end" className="w-56 p-1">
        <ul>
          {HIDEABLE_COLUMNS.map(({ key, label }) => {
            const shown = !hidden.has(key);
            return (
              <li key={key}>
                <button
                  type="button"
                  aria-pressed={shown}
                  onClick={() => onToggle(key)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  <span className="min-w-0 flex-1 truncate">{label}</span>
                  {shown && (
                    <Check className="size-4 shrink-0 text-slate-500" aria-hidden />
                  )}
                </button>
              </li>
            );
          })}
        </ul>

        {/* Nothing to bring back when the panorama is whole: an action that
            would do nothing is not offered. */}
        {hidden.size > 0 && (
          <>
            <hr className="my-1 border-slate-200" />
            <button
              type="button"
              onClick={onShowAll}
              className="w-full cursor-pointer rounded px-2 py-1.5 text-left text-sm text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
            >
              Tout afficher
            </button>
          </>
        )}
      </PopoverContent>
    </Popover>
  );
}
