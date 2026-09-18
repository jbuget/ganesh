"use client";

import type { ProjectCategory } from "@/lib/api/generated/model";
import { category } from "@/lib/board";

interface CategoryMarkProps {
  value: ProjectCategory | null | undefined;
}

/**
 * A mission's strategic axis: a coloured bullet, an ordinary label.
 *
 * Square, where a phase's dot is round: on one line, two marks of the same
 * shape would read as the same information.
 */
export function CategoryMark({ value }: CategoryMarkProps) {
  const axis = category(value);
  if (!axis) return null;

  return (
    <span className="flex items-center gap-1.5 text-slate-700">
      <span className={`size-2.5 shrink-0 rounded-[3px] ${axis.bullet}`} aria-hidden />
      {axis.label}
    </span>
  );
}
