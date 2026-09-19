"use client";

import { ChevronRight } from "lucide-react";
import { useState } from "react";

import type { ProjectContributionResponse } from "@/lib/api/generated/model";
import { formatDecimalDays, formatMonth } from "@/lib/dates";

interface ProjectContributionsProps {
  contributions: ProjectContributionResponse[];
  total: number;
}

/**
 * Who consumed what on a mission.
 *
 * A list rather than a table: two to six people are on a mission, and what one
 * reads there is a share, not a grid of figures. The monthly detail unfolds
 * under the row rather than opening a screen: the other contributors stay
 * before the eyes, and they are what one compares against.
 */
export function ProjectContributions({
  contributions,
  total,
}: ProjectContributionsProps) {
  // Several rows stay open at once: two contributors are expanded precisely to
  // set their months side by side.
  const [expanded, setExpanded] = useState<ReadonlySet<number>>(new Set());

  function toggle(memberId: number) {
    setExpanded((current) => {
      const next = new Set(current);
      if (!next.delete(memberId)) next.add(memberId);
      return next;
    });
  }

  if (contributions.length === 0) {
    return <p className="text-sm text-slate-400">Aucun temps déclaré</p>;
  }

  return (
    <ul className="space-y-0.5">
      {contributions.map((contribution) => {
        const isOpen = expanded.has(contribution.member.id);
        const part = total > 0 ? (contribution.days / total) * 100 : 0;

        return (
          <li key={contribution.member.id}>
            <button
              type="button"
              aria-expanded={isOpen}
              onClick={() => toggle(contribution.member.id)}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-1 py-1.5 text-left transition-colors hover:bg-slate-50"
            >
              <ChevronRight
                aria-hidden
                className={`size-3.5 shrink-0 text-slate-400 transition-transform ${isOpen ? "rotate-90" : ""}`}
              />
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
                {contribution.member.initials}
              </span>
              <span className="min-w-0 flex-1 truncate text-sm text-slate-700">
                {contribution.member.display_name}
              </span>
              <span
                aria-hidden
                className="hidden h-1.5 w-24 shrink-0 overflow-hidden rounded-full bg-slate-100 sm:block"
              >
                <span
                  className="block h-full rounded-full bg-sky-500"
                  style={{ width: `${part}%` }}
                />
              </span>
              <span className="w-16 shrink-0 text-right text-sm tabular-nums text-slate-600">
                {formatDecimalDays(contribution.days)} jrs.
              </span>
            </button>

            {isOpen && (
              <ul className="mt-0.5 mb-1 ml-[3.25rem] space-y-0.5">
                {contribution.by_month.map((month) => (
                  <li
                    key={month.month}
                    className="flex items-center gap-2 text-sm text-slate-500"
                  >
                    <span className="min-w-0 flex-1 truncate capitalize">
                      {formatMonth(
                        Number(month.month.slice(0, 4)),
                        Number(month.month.slice(5, 7)),
                      )}
                    </span>
                    <span className="w-16 shrink-0 text-right tabular-nums">
                      {formatDecimalDays(month.days)} jrs.
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </li>
        );
      })}
    </ul>
  );
}
