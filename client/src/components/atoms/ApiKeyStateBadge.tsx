import type { ApiKeyResponse } from "@/lib/api/generated/model";
import { STATES } from "@/lib/api-keys";

/**
 * What a key is worth right now.
 *
 * The state comes from the server rather than being recomputed here: an
 * expiry read two ways would eventually read two ways.
 */
export function ApiKeyStateBadge({ state }: { state: ApiKeyResponse["state"] }) {
  const shown = STATES[state] ?? { label: state, dot: "bg-slate-300" };

  return (
    <span className="inline-flex items-center gap-1.5 text-sm text-slate-700">
      <span className={`size-2 shrink-0 rounded-full ${shown.dot}`} aria-hidden />
      {shown.label}
    </span>
  );
}
