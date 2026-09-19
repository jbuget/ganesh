interface MetricTileProps {
  label: string;
  value: string;
  /** What makes the figure readable: its denominator, its detail. */
  hint?: string;
  /** `warning` for a figure worth going to look at. Never an error. */
  tone?: "plain" | "warning";
}

/**
 * One figure, named, with what it is measured against.
 *
 * The hint is not decoration: « 75 % » says nothing, « 75 %, 9 months out of
 * 12 » can be acted upon.
 */
export function MetricTile({ label, value, hint, tone = "plain" }: MetricTileProps) {
  return (
    <div
      data-tone={tone}
      className={[
        "rounded-lg border px-4 py-3",
        tone === "warning"
          ? "border-amber-300 bg-amber-50"
          : "border-slate-200 bg-white",
      ].join(" ")}
    >
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-1 text-xl font-semibold tabular-nums text-slate-900">
        {value}
      </dd>
      {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
