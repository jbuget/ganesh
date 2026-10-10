import { formatPersonDays, formatShare, type BarSegment } from "@/lib/statistics";

interface StackedBarProps {
  segments: BarSegment[];
  /** Names the bar for whoever reads it aloud. */
  label: string;
}

/**
 * One bar split into the parts of a whole, with a legend that carries the figures.
 *
 * A single bar rather than a pie: it reads straight across, and two windows
 * laid one under the other can be compared by eye. The legend is always
 * there — colour alone never carries which part is which — and wears the
 * text colours, with a swatch beside it for identity. A thin gap in the
 * surface colour separates the parts.
 */
export function StackedBar({ segments, label }: StackedBarProps) {
  return (
    <div>
      <div role="img" aria-label={label} className="flex h-3 gap-0.5">
        {segments.map((segment) => (
          <div
            key={segment.key}
            style={{
              width: `${segment.share * 100}%`,
              backgroundColor: segment.colour,
            }}
            className="first:rounded-l last:rounded-r"
          />
        ))}
      </div>

      <ul className="mt-3 space-y-1.5">
        {segments.map((segment) => (
          <li
            key={segment.key}
            className="grid grid-cols-[auto_1fr_auto_auto] items-center gap-x-2 text-sm"
          >
            <span
              aria-hidden
              style={{ backgroundColor: segment.colour }}
              className="size-2.5 rounded-sm"
            />
            <span className="truncate text-slate-700">{segment.label}</span>
            <span className="tabular-nums text-slate-500">
              {formatPersonDays(segment.days)} j
            </span>
            <span className="w-12 text-right font-medium tabular-nums text-slate-900">
              {formatShare(segment.share)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
