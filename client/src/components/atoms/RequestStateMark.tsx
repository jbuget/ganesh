"use client";

import type { RequestState } from "@/lib/api/generated/model";
import { requestStateDot, requestStateLabel } from "@/lib/requests";

interface RequestStateMarkProps {
  value: RequestState;
}

/**
 * Where a need stands: a coloured dot, an ordinary label.
 *
 * Round, as a phase's dot is: a request carries one mark and never two, so
 * nothing on its line can be taken for something else.
 */
export function RequestStateMark({ value }: RequestStateMarkProps) {
  return (
    <span className="flex items-center gap-1.5 text-slate-700">
      <span
        className={`size-2.5 shrink-0 rounded-full ${requestStateDot(value)}`}
        aria-hidden
      />
      {requestStateLabel(value)}
    </span>
  );
}
