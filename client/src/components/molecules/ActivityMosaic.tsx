"use client";

import { useEffect, useRef } from "react";

import { ActivityCell } from "@/components/atoms/ActivityCell";
import { ActivityDayDetail } from "@/components/atoms/ActivityDayDetail";
import type { ActivityDayResponse } from "@/lib/api/generated/model";
import {
  type ActivityLevel,
  activityLevel,
  activityMonthLabels,
  activityWeeks,
  describeActivityDay,
  formatGestures,
} from "@/lib/statistics";
import { useCursorTooltip } from "@/lib/use-cursor-tooltip";

interface ActivityMosaicProps {
  /** Every day of the year ending today, oldest first, quiet ones included. */
  days: ActivityDayResponse[];
}

const WEEKDAY_LABELS = ["Lun", "", "Mer", "", "Ven", "", ""];

const LEVELS: ActivityLevel[] = [0, 1, 2, 3, 4];

/**
 * The gestures of the year as a calendar, in the manner of GitHub's: one
 * column per week, one cell per day, darker the more the register holds.
 *
 * Every gesture counts, whoever made it. The mosaic answers « was the
 * product lived in that day », and which function it was is the table's
 * business, further down the page.
 *
 * A day opens its detail the moment the pointer reaches it, where the native
 * tooltip would keep one waiting: a year of cells is explored by sweeping
 * across it, not by pausing on each.
 */
export function ActivityMosaic({ days }: ActivityMosaicProps) {
  const { tooltip, follow, leave } = useCursorTooltip({ rich: true });
  const total = days.reduce((sum, entry) => sum + entry.gestures, 0);
  const busiest = Math.max(0, ...days.map((entry) => entry.gestures));
  const weeks = activityWeeks(days);
  const months = activityMonthLabels(weeks);
  const scroller = useRef<HTMLDivElement>(null);

  // On a narrow screen the year does not fit: what is read first is the
  // latest weeks, so the window opens on the right.
  useEffect(() => {
    if (scroller.current) scroller.current.scrollLeft = scroller.current.scrollWidth;
  }, [days]);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-medium text-slate-900">Gestes au jour le jour</h3>

      {total === 0 ? (
        <p className="mt-1 text-sm text-slate-500">Aucun geste sur la période.</p>
      ) : (
        <p className="mt-1 text-sm text-slate-500">
          {formatGestures(total)} sur l&apos;année écoulée
        </p>
      )}

      <div ref={scroller} className="mt-3 flex gap-2 overflow-x-auto pb-1">
        <div
          aria-hidden
          className="grid grid-rows-[1rem_repeat(7,0.75rem)] gap-[2px] pr-1 text-[10px] leading-3 text-slate-500"
        >
          <span />
          {WEEKDAY_LABELS.map((label, row) => (
            <span key={row}>{label}</span>
          ))}
        </div>

        <div className="flex gap-[2px]">
          {weeks.map((week, column) => (
            <div
              key={column}
              className="grid grid-rows-[1rem_repeat(7,0.75rem)] gap-[2px]"
            >
              <span aria-hidden className="relative">
                <span className="absolute top-0 left-0 text-[10px] leading-4 whitespace-nowrap text-slate-500">
                  {months[column]}
                </span>
              </span>
              {week.map((entry, row) =>
                entry ? (
                  <ActivityCell
                    key={row}
                    level={activityLevel(entry.gestures, busiest)}
                    role="img"
                    aria-label={describeActivityDay(entry)}
                    onMouseEnter={(event) =>
                      follow(
                        event,
                        <ActivityDayDetail
                          day={entry.day}
                          gestures={entry.gestures}
                          busiest={busiest}
                          total={total}
                        />,
                      )
                    }
                    onMouseLeave={leave}
                  />
                ) : (
                  <span key={row} aria-hidden className="size-3" />
                ),
              )}
            </div>
          ))}
        </div>
      </div>

      <div
        aria-hidden
        className="mt-2 flex items-center justify-end gap-1 text-[10px] text-slate-500"
      >
        <span>Moins</span>
        {LEVELS.map((level) => (
          <ActivityCell key={level} level={level} />
        ))}
        <span>Plus</span>
      </div>

      {tooltip}
    </section>
  );
}
