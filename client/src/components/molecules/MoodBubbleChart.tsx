"use client";

import { MoodAverageLine } from "@/components/atoms/MoodAverageLine";
import { MoodBubble } from "@/components/atoms/MoodBubble";
import type { DayMoodsResponse } from "@/lib/api/generated/model";
import { formatWeek, formatWeekdayDate } from "@/lib/dates";
import { MOODS } from "@/lib/mood";
import { useCursorTooltip } from "@/lib/use-cursor-tooltip";

interface MoodBubbleChartProps {
  /** The days of the window, the most recent first, as the API hands them over. */
  days: DayMoodsResponse[];
}

/**
 * The fortnight as a field of bubbles: one band per level, one column per day.
 *
 * Where a table gives a day at a time, the chart gives the whole window at
 * once — a bad patch is a weight sinking to the bottom bands over several
 * columns, which no row read one by one would show.
 *
 * The bands climb, the best on top: up is better, as on any axis. The days run
 * the other way round from the record beside them — oldest on the left — for
 * the same reason: time runs left to right, and a window read backwards would
 * make every drift look like a recovery.
 */
export function MoodBubbleChart({ days }: MoodBubbleChartProps) {
  const { tooltip, follow, leave } = useCursorTooltip();

  const columns = [...days].reverse();
  // The best on top: `MOODS` is declared from the worst up.
  const bands = [...MOODS].reverse();

  const busiest = Math.max(
    1,
    ...columns.flatMap((day) => bands.map((band) => day.counts[band.value] ?? 0)),
  );

  return (
    <div className="space-y-2">
      <div className="flex" onMouseLeave={leave}>
        <div className="w-32 shrink-0">
          {bands.map((band) => {
            const Icon = band.icon;

            return (
              <div key={band.value} className="flex h-14 items-center gap-1.5">
                <Icon className={`size-5 shrink-0 ${band.colour}`} aria-hidden />
                <span className="text-xs text-slate-600">{band.label}</span>
              </div>
            );
          })}
        </div>

        <div className="relative min-w-0 flex-1">
          {bands.map((band) => (
            <div
              key={band.value}
              className="flex h-14 items-center border-b border-slate-100 last:border-b-0"
            >
              {columns.map((day) => {
                const count = day.counts[band.value] ?? 0;

                return (
                  <span
                    key={day.day}
                    className="flex flex-1 justify-center"
                    onMouseMove={(event) =>
                      count > 0 &&
                      follow(
                        event,
                        `${band.label} · ${count} réponse${count > 1 ? "s" : ""} le ${formatWeekdayDate(day.day)}`,
                      )
                    }
                  >
                    <MoodBubble level={band.value} count={count} busiest={busiest} />
                  </span>
                );
              })}
            </div>
          ))}

          <MoodAverageLine
            averages={columns.map((day) => day.average)}
            bands={bands.length}
          />
        </div>
      </div>

      <div className="flex">
        <div className="w-32 shrink-0" />
        <div className="flex min-w-0 flex-1">
          {columns.map((day) => (
            <span
              key={day.day}
              className="flex-1 truncate text-center text-xs text-slate-500"
            >
              {formatWeek(day.day)}
            </span>
          ))}
        </div>
      </div>

      <p className="pl-32 text-xs text-slate-400">
        <span className="mr-1.5 inline-block h-0.5 w-4 translate-y-[-3px] bg-slate-600" />
        Moyenne du jour
      </p>

      {tooltip}
    </div>
  );
}
