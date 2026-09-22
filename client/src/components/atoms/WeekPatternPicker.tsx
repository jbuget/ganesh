"use client";

import { WEEKDAYS, type WeekPattern, formatDayValue, nextValue } from "@/lib/rhythm";

interface WeekPatternPickerProps {
  pattern: WeekPattern;
  /**
   * Whether the reader may change it.
   *
   * Everyone declares their own rhythm and nobody else's, so this is false on
   * a colleague's panel — where the motif is still worth reading: knowing that
   * somebody is off on Wednesdays is what staffing them rests on.
   */
  editable?: boolean;
  onChange?: (pattern: WeekPattern) => void;
}

/** How full a day of the motif reads. Height carries it, not colour alone. */
function fillOf(value: number): string {
  if (value >= 1) return "bg-sky-600 text-white";
  if (value >= 0.5)
    return "bg-gradient-to-t from-sky-600 from-50% to-slate-100 to-50% text-slate-900";
  return "bg-slate-100 text-slate-400";
}

/**
 * The five days of an ordinary week, and how much of each one works.
 *
 * A click takes a day down — full day, half day, nothing, and back round: a
 * motif is read as the exception to a full week, so one opens this to take
 * days off rather than to add them.
 *
 * It says what is *expected*, never what is allowed. Somebody off on
 * Wednesdays may swap one for a Thursday, and the grid takes that entry
 * without a word: the rhythm holds the week's total, which a swap leaves
 * untouched.
 */
export function WeekPatternPicker({
  pattern,
  editable = false,
  onChange,
}: WeekPatternPickerProps) {
  return (
    <ul className="flex gap-1.5">
      {WEEKDAYS.map((day, index) => {
        const value = pattern[day.key];
        const said = `${day.label} : ${formatDayValue(value)}`;

        return (
          <li key={day.key}>
            {editable ? (
              <button
                type="button"
                title={said}
                aria-label={said}
                onClick={() => onChange?.({ ...pattern, [day.key]: nextValue(value) })}
                className={`flex size-9 cursor-pointer items-center justify-center rounded border border-slate-300 text-sm font-medium transition-opacity hover:opacity-80 ${fillOf(value)}`}
              >
                {day.initial}
                {/* Two Mondays-of-the-middle-of-the-week read alike as a
                    letter: the position says which, and the label says it
                    outright to whoever cannot see the row. */}
                <span className="sr-only">{` (${index + 1}e jour)`}</span>
              </button>
            ) : (
              <span
                title={said}
                aria-label={said}
                className={`flex size-9 items-center justify-center rounded border border-slate-300 text-sm font-medium ${fillOf(value)}`}
              >
                {day.initial}
              </span>
            )}
          </li>
        );
      })}
    </ul>
  );
}
