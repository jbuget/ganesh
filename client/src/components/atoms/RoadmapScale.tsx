import { monthsOf, positionOf } from "@/lib/roadmap";

interface RoadmapScaleProps {
  from: string;
  to: string;
  /** The day the drawing was made, where the rule is placed. */
  today: string;
}

/**
 * The axis of months the bars are read against.
 *
 * Each month takes its real width rather than an equal share: February is
 * shorter than March, and a scale pretending otherwise would put every bar a
 * couple of days off its date.
 *
 * The « aujourd'hui » rule runs the full height of the drawing, which is why
 * it is drawn by the timeline around this and not here: a rule stopping at
 * the header would say nothing about where the bars stand.
 */
export function RoadmapScale({ from, to, today }: RoadmapScaleProps) {
  const months = monthsOf(from, to);
  const rule = positionOf(today, from, to);
  const showsRule = rule >= 0 && rule <= 1;

  return (
    <div className="relative flex border-b border-slate-300">
      {months.map((month) => (
        <div
          key={month.key}
          style={{ width: `${month.width * 100}%` }}
          className="min-w-0 border-l border-slate-200 px-1 py-1 first:border-l-0"
        >
          {/* The month alone. A window runs from the month before today to a
              handful ahead: which year each one belongs to is never in doubt,
              and spelling it out would crowd a column of four characters. */}
          <span className="block truncate text-xs text-slate-500">{month.label}</span>
        </div>
      ))}

      {showsRule && (
        <span
          aria-hidden
          style={{ left: `${rule * 100}%` }}
          className="absolute -top-0.5 size-1.5 -translate-x-1/2 rounded-full bg-sky-600"
        />
      )}
    </div>
  );
}
