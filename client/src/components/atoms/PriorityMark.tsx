"use client";

import type { ProjectPriority } from "@/lib/api/generated/model";
import { priority } from "@/lib/board";

interface PriorityMarkProps {
  value: ProjectPriority | null | undefined;
}

/**
 * A mission's urgency: a coloured gauge, an ordinary label.
 *
 * How full the gauge is carries the scale as much as the shade does — four
 * bars, then three, two, one — so that it reads without the colour.
 */
export function PriorityMark({ value }: PriorityMarkProps) {
  const urgency = priority(value);
  if (!urgency) return null;

  const Icon = urgency.icon;

  return (
    <span className="flex items-center gap-1.5 text-slate-700">
      <Icon className={`size-4 shrink-0 ${urgency.colour}`} aria-hidden />
      {urgency.label}
    </span>
  );
}
