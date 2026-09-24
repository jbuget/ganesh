"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ProjectCategory } from "@/lib/api/generated/model";
import { CATEGORIES, category } from "@/lib/board";

interface CategoryPickerProps {
  value: ProjectCategory | null | undefined;
  /**
   * Whether the reader may change it.
   *
   * Editable by default: a field one cannot change is the exception, and it
   * is the screen holding the field that knows — a guest reads every sheet of
   * the reference list and rewrites none.
   */
  editable?: boolean;
  onChange: (value: ProjectCategory | null) => void | Promise<void>;
}

/** A mission's strategic axis. One, or none. */
export function CategoryPicker({
  value,
  editable = true,
  onChange,
}: CategoryPickerProps) {
  const [isOpen, setOpen] = useState(false);
  const axis = category(value);

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label="Changer la catégorie"
        disabled={!editable}
        className={`-mx-1 flex ${editable ? "cursor-pointer" : ""} items-center rounded px-1 py-0.5 transition-colors ${editable ? "hover:bg-slate-100" : ""}`}
      >
        {axis ? (
          <span className="flex items-center gap-1.5 text-sm text-slate-700">
            <span
              className={`size-2.5 shrink-0 rounded-[3px] ${axis.bullet}`}
              aria-hidden
            />
            {axis.label}
          </span>
        ) : (
          <span className="flex items-center gap-1 text-sm text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            Catégorie
          </span>
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-64 p-1">
        <ul>
          {CATEGORIES.map((choice) => (
            <li key={choice.value}>
              <button
                type="button"
                aria-pressed={choice.value === value}
                onClick={() => {
                  setOpen(false);
                  // Clicking the current axis again removes it: the only way
                  // back to « no category ».
                  void onChange(choice.value === value ? null : choice.value);
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <span
                  className={`size-2.5 shrink-0 rounded-[3px] ${choice.bullet}`}
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
