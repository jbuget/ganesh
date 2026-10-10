interface CountBarProps {
  label: string;
  count: number;
  /** The largest count among the lines: the one that fills the track. */
  max: number;
}

const SERIES = "#2a78d6";

/**
 * One line of a count: what it is, how many, and a bar placing it against the others.
 *
 * The figure stands without the bar, which only sets the lines against each
 * other. Every line is the same series, so there is no colour to explain.
 */
export function CountBar({ label, count, max }: CountBarProps) {
  const width = max === 0 ? 0 : (count / max) * 100;

  return (
    <div className="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-1">
      <span className="truncate text-sm text-slate-700">{label}</span>
      <span className="text-right text-sm font-medium tabular-nums text-slate-900">
        {count}
      </span>

      <div className="col-span-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div
          role="meter"
          aria-label={label}
          aria-valuenow={count}
          aria-valuemin={0}
          aria-valuemax={max}
          style={{ width: `${width}%`, backgroundColor: SERIES }}
          className="h-full rounded-full"
        />
      </div>
    </div>
  );
}
