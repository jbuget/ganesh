"use client";

import { ChevronRight } from "lucide-react";
import { useState } from "react";

import { DigestFactLine } from "@/components/atoms/DigestFactLine";
import type { ChapterResponse, MovementKind } from "@/lib/api/generated/model";
import { formatShortDate } from "@/lib/dates";
import { chapterLine, chapterTitle } from "@/lib/gazette";

interface DigestChaptersProps {
  chapters: ChapterResponse[];
}

/**
 * The tint of each kind of movement.
 *
 * It follows what the fact means, not what it is about: a mise en service is
 * green wherever it appears, a step backwards amber. Anything that merely
 * happened stays slate — colour marks what deserves marking, and a list where
 * every line is coloured marks nothing.
 */
const DOTS: Record<MovementKind, string> = {
  project_created: "bg-sky-500",
  project_archived: "bg-slate-400",
  project_revived: "bg-sky-500",
  phase_advanced: "bg-slate-300",
  phase_stepped_back: "bg-amber-500",
  went_live: "bg-emerald-500",
  news_posted: "bg-slate-300",
  teammate_joined: "bg-violet-500",
  teammate_returned: "bg-violet-500",
  teammate_left: "bg-slate-400",
};

/**
 * The month, project by project, each one day after day.
 *
 * Gathered rather than flat: a single list of everything that happened reads
 * as the log it came from, where the same project is picked up and dropped
 * ten times over. Under its own heading, a project's month reads as a story —
 * and a work package's facts are told among its project's, because a lot's
 * month is part of its project's month, not a chronicle of its own.
 *
 * Closed to begin with, all of them. A month of tidying-up touches a dozen
 * projects, and a dozen chronicles unfolded bury the two that had something
 * to say. Folded, the section is first read as what it is — the list of
 * projects the month touched, and how much happened to each.
 */
export function DigestChapters({ chapters }: DigestChaptersProps) {
  const [opened, setOpened] = useState<(number | null)[]>([]);

  return (
    <ul className="overflow-hidden rounded-lg border border-slate-200">
      {chapters.map((chapter) => {
        const isOpen = opened.includes(chapter.project_id);
        const title = chapterTitle(chapter);

        return (
          <li
            key={chapter.project_id ?? "team"}
            className="border-b border-slate-100 last:border-b-0"
          >
            <button
              type="button"
              aria-expanded={isOpen}
              className="flex w-full cursor-pointer items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-slate-50"
              onClick={() =>
                setOpened((open) =>
                  isOpen
                    ? open.filter((it) => it !== chapter.project_id)
                    : [...open, chapter.project_id],
                )
              }
            >
              <ChevronRight
                className={`size-4 shrink-0 text-slate-400 transition-transform ${
                  isOpen ? "rotate-90" : ""
                }`}
                aria-hidden
              />
              <span className="min-w-0 flex-1 truncate text-sm text-slate-900">
                {title}
              </span>
              <span className="shrink-0 text-xs tabular-nums text-slate-500">
                {chapter.movements.length}
              </span>
            </button>

            {isOpen && (
              <ul className="px-3 pb-2 pl-9">
                {chapter.movements.map((movement, rank) => (
                  <DigestFactLine
                    key={`${movement.at}-${movement.kind}-${rank}`}
                    sentence={chapterLine(movement, chapter)}
                    dot={DOTS[movement.kind] ?? "bg-slate-300"}
                    when={formatShortDate(movement.at)}
                  />
                ))}
              </ul>
            )}
          </li>
        );
      })}
    </ul>
  );
}
