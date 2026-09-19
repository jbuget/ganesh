import { NOTHING, formatPersonDays, formatShare } from "@/lib/statistics";

interface ShareBarProps {
  label: string;
  days: number;
  /** Weight in the window, or null when nothing was declared. */
  share: number | null | undefined;
  /** Tailwind background, to keep the colour a phase or an axis carries elsewhere. */
  colour?: string;
}

/**
 * One line of a breakdown: what it is, how many days, what share.
 *
 * The figures come before the bar, and stand without it: the bar places the
 * lines against each other, it does not carry the reading on its own.
 */
export function ShareBar({
  label,
  days,
  share,
  colour = "bg-slate-400",
}: ShareBarProps) {
  const known = share !== null && share !== undefined;

  return (
    <div className="grid grid-cols-[1fr_auto_auto] items-center gap-x-3 gap-y-1">
      <span className="truncate text-sm text-slate-700">{label}</span>
      <span className="text-sm tabular-nums text-slate-500">
        {formatPersonDays(days)} j
      </span>
      <span className="w-12 text-right text-sm font-medium tabular-nums text-slate-900">
        {known ? formatShare(share) : NOTHING}
      </span>

      {known && (
        <div className="col-span-3 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div
            role="meter"
            aria-label={label}
            aria-valuenow={Math.round(share * 100)}
            aria-valuemin={0}
            aria-valuemax={100}
            style={{ width: `${Math.round(share * 100)}%` }}
            className={`h-full rounded-full ${colour}`}
          />
        </div>
      )}
    </div>
  );
}
