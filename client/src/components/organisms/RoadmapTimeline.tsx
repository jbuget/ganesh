"use client";

import { ChevronRight } from "lucide-react";
import { useState } from "react";

import { RoadmapScale } from "@/components/atoms/RoadmapScale";
import { RoadmapRow } from "@/components/molecules/RoadmapRow";
import type { RoadmapMissionResponse } from "@/lib/api/generated/model";
import { bandsOf, positionOf, silentNotice, type Grouping } from "@/lib/roadmap";

interface RoadmapTimelineProps {
  missions: RoadmapMissionResponse[];
  from: string;
  to: string;
  today: string;
  grouping: Grouping;
  /** Opens a mission beside the drawing. */
  onOpen: (projectId: number) => void;
  onDate: (projectId: number, target: string | null) => void | Promise<void>;
}

/** Width of the three fixed columns, so the rule lines up with the bars. */
const HEADINGS = "w-72 shrink-0";
const DATES = "w-36 shrink-0";
const SLIPPAGE = "w-32 shrink-0";

/**
 * The whole drawing: an axis of months, bands of missions, one bar each.
 *
 * It fits the width it is given rather than scrolling sideways. A roadmap is
 * shown — to a committee, to a department — and something one has to scroll
 * to read whole is not shown, it is consulted.
 *
 * The « aujourd'hui » rule runs the full height, behind the bars: it is what
 * separates what happened from what is supposed, and a mark confined to the
 * header would say nothing about where any bar stands against it.
 */
export function RoadmapTimeline({
  missions,
  from,
  to,
  today,
  grouping,
  onOpen,
  onDate,
}: RoadmapTimelineProps) {
  const bands = bandsOf(missions, grouping);
  const rule = positionOf(today, from, to);
  const showsRule = rule >= 0 && rule <= 1;

  //: Which bands have had their silent lines opened. Folded by default, and
  //: one band at a time: one goes looking for what is missing on a single
  //: axis, not across the whole portfolio at once.
  const [unfolded, setUnfolded] = useState<Set<string>>(new Set());

  function toggle(key: string) {
    setUnfolded((open) => {
      const next = new Set(open);
      if (!next.delete(key)) next.add(key);
      return next;
    });
  }

  if (bands.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        Aucune mission à montrer sur cette période.
      </p>
    );
  }

  return (
    // The scale stays put while the bands move under it. Sixty lines deep,
    // a reader who has lost the months no longer knows what they are looking
    // at: the axis is the reading, not an ornament at the top of it.
    <div className="flex h-full min-h-0 flex-col rounded-md border border-slate-300 bg-white">
      <div className="flex shrink-0 items-end border-b border-slate-300 bg-slate-50">
        <div className={`${HEADINGS} px-3 py-1`}>
          <span className="text-xs text-slate-500">Mission</span>
        </div>
        <div className={`${DATES} pr-3 py-1`}>
          <span className="text-xs text-slate-500">Annoncée</span>
        </div>
        <div className="min-w-0 flex-1 pr-3">
          <RoadmapScale from={from} to={to} today={today} />
        </div>
        <div className={`${SLIPPAGE} pr-3 py-1 text-right`}>
          <span className="text-xs text-slate-500">Écart</span>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {/* Positioned here and not on the scroller: `inset-0` covers what its
            positioned parent covers, and the rule has to run the whole height
            of the content, not of the window onto it. */}
        <div className="relative">
          {/* The rule is drawn on a layer laid out exactly like a row: same
            columns, same widths, same padding. Placing it with a calc() over
            the whole table would mean restating those widths somewhere else,
            and the two would drift apart the first time one changed. */}
          <div aria-hidden className="pointer-events-none absolute inset-0 flex">
            <div className={HEADINGS} />
            <div className={DATES} />
            <div className="relative min-w-0 flex-1 pr-3">
              {showsRule && (
                <span
                  style={{ left: `${rule * 100}%` }}
                  className="absolute inset-y-0 w-px bg-sky-300"
                />
              )}
            </div>
            <div className={SLIPPAGE} />
          </div>

          {bands.map((band) => (
            <section key={band.key}>
              <h3 className="flex items-center gap-2 border-b border-slate-200 bg-slate-50/70 px-3 py-1">
                {band.mark && (
                  <span
                    aria-hidden
                    className={`size-2 shrink-0 ${band.mark} rounded-sm`}
                  />
                )}
                <span className="text-xs font-medium tracking-wide text-slate-600 uppercase">
                  {band.label}
                </span>
                <span className="text-xs text-slate-400">{band.missions.length}</span>
              </h3>

              <div>
                {band.speaking.map((mission) => (
                  <RoadmapRow
                    key={mission.project_id}
                    mission={mission}
                    from={from}
                    to={to}
                    onOpen={onOpen}
                    onDate={onDate}
                  />
                ))}

                {/* A mission nobody estimated and nobody dated is a fact
                    about the portfolio, not a line worth a row of its own:
                    counted and folded, forty of them stop drowning the dozen
                    that have something to say. */}
                {band.silent.length > 0 && (
                  <>
                    <button
                      type="button"
                      aria-expanded={unfolded.has(band.key)}
                      onClick={() => toggle(band.key)}
                      className="flex w-full cursor-pointer items-center gap-1.5 border-b border-slate-100 px-3 py-1.5 text-left text-xs text-slate-400 transition-colors hover:bg-slate-50 hover:text-slate-600"
                    >
                      <ChevronRight
                        aria-hidden
                        className={[
                          "size-3.5 shrink-0 transition-transform",
                          unfolded.has(band.key) ? "rotate-90" : "",
                        ].join(" ")}
                      />
                      {silentNotice(band.silent.length)}
                    </button>

                    {unfolded.has(band.key) &&
                      band.silent.map((mission) => (
                        <RoadmapRow
                          key={mission.project_id}
                          mission={mission}
                          from={from}
                          to={to}
                          onOpen={onOpen}
                          onDate={onDate}
                        />
                      ))}
                  </>
                )}
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
