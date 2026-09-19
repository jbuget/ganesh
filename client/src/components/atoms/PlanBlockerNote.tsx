import { AlertTriangle } from "lucide-react";

import type { PlanBlocker } from "@/lib/api/generated/model";
import { blocker } from "@/lib/planning";

interface PlanBlockerNoteProps {
  reason: PlanBlocker;
}

/**
 * Why a mission carries no date, and what to do about it.
 *
 * Said out loud rather than dropped from the list: a mission nobody estimated
 * is exactly the one steering needs to see, and a plan that quietly left it
 * out would read as complete when it is not.
 */
export function PlanBlockerNote({ reason }: PlanBlockerNoteProps) {
  const said = blocker(reason);
  if (!said) return null;

  return (
    <span className="flex items-center gap-1.5" title={said.hint}>
      <AlertTriangle aria-hidden className="size-3.5 shrink-0 text-amber-500" />
      <span className="text-sm text-slate-500">{said.label}</span>
    </span>
  );
}
