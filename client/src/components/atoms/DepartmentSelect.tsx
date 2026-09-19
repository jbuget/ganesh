"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Department } from "@/lib/api/generated/model";
import { DEPARTMENTS, departmentLabel } from "@/lib/departments";

interface DepartmentSelectProps {
  value: Department | null | undefined;
  /** Without the right to write, the department reads and no more. */
  editable: boolean;
  onChange: (value: Department | null) => void | Promise<void>;
}

/**
 * The department a teammate belongs to.
 *
 * One only, where a mission may serve several: one works in a department, one
 * does not belong to two. The list is the missions' own — steering compares
 * the two sides, and could not if the names drifted apart.
 */
export function DepartmentSelect({ value, editable, onChange }: DepartmentSelectProps) {
  const [isOpen, setOpen] = useState(false);
  const current = value ?? null;

  function choose(next: Department | null) {
    setOpen(false);
    if (next !== current) void onChange(next);
  }

  if (!editable) {
    return current ? (
      <span className="text-sm text-slate-700">{departmentLabel(current)}</span>
    ) : (
      <span className="text-sm text-slate-400">Non renseigné</span>
    );
  }

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={
          current
            ? `Changer le département, actuellement ${departmentLabel(current)}`
            : "Choisir un département"
        }
        className="-mx-1 flex cursor-pointer items-center rounded px-1 py-0.5 text-sm transition-colors hover:bg-slate-100"
      >
        {current ? (
          <span className="text-slate-700">{departmentLabel(current)}</span>
        ) : (
          <span className="flex items-center gap-1 text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            Département
          </span>
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-64 p-1">
        <ul>
          {/* First, and named: a department taken back off is a choice like
              any other, and hunting for it at the bottom of ten lines is not. */}
          <li>
            <button
              type="button"
              aria-pressed={current === null}
              onClick={() => choose(null)}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm text-slate-500 transition-colors hover:bg-slate-100"
            >
              <span className="min-w-0 flex-1 truncate">Aucun</span>
              {current === null && (
                <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
              )}
            </button>
          </li>

          {DEPARTMENTS.map((department) => (
            <li key={department.value}>
              <button
                type="button"
                aria-pressed={department.value === current}
                onClick={() => choose(department.value)}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <span className="min-w-0 flex-1 truncate">{department.label}</span>
                {department.value === current && (
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
