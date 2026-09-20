"use client";

import { Check } from "lucide-react";
import Link from "next/link";

import type { MonthFillingResponse } from "@/lib/api/generated/model";
import { formatDecimalDays } from "@/lib/dates";
import { readMonths } from "@/lib/user-record";

interface UserMonthsProps {
  months: MonthFillingResponse[];
  /** Whose sheets these are: each row opens that person's month. */
  userId: number;
  /** Injected: a render dated by `new Date()` could not be tested. */
  today: string;
}

/**
 * Where somebody's monthly sheets stand, over the last six months.
 *
 * The question a manager opens a teammate for, and one that had no answer
 * anywhere but by opening each month in turn. A month running is measured
 * against the days already gone, never against the whole of it, or every
 * reading before the 30th would look like a delay.
 *
 * Each row opens that month for that person, which is what one does next
 * when a figure is missing.
 */
export function UserMonths({ months, userId, today }: UserMonthsProps) {
  return (
    <ul className="space-y-0.5">
      {readMonths(months, today).map((month) => (
        <li key={month.month}>
          <Link
            href={`/timesheet?month=${month.month.slice(0, 7)}&user=${userId}`}
            className="flex cursor-pointer flex-col gap-1 rounded px-1 py-1.5 transition-colors hover:bg-slate-50"
          >
            <span className="flex items-baseline gap-2">
              <span className="min-w-0 flex-1 truncate text-sm text-slate-700 capitalize">
                {month.label}
              </span>

              {/* Against the working days of the whole month, running or not:
                  a denominator that moved with the date would make the same
                  month read two ways in a fortnight. What is owed so far is
                  said below, where the days already gone are counted. */}
              <span className="shrink-0 text-sm tabular-nums text-slate-600">
                {formatDecimalDays(month.delivered)} j
                <span className="text-slate-400"> / {month.workingDays} j</span>
              </span>
            </span>

            <span
              className="flex h-1.5 overflow-hidden rounded-full bg-slate-200"
              role="presentation"
            >
              <span
                className="bg-slate-700"
                style={{ width: `${month.deliveredShare}%` }}
              />
              <span
                className="bg-slate-300"
                style={{ width: `${month.forecastShare}%` }}
              />
            </span>

            <span className="flex items-baseline gap-2 text-xs">
              {/* What this month is still waiting for, named by the gesture it
                  calls for: a month with days missing is filled in, a month
                  already over and complete is closed. */}
              <span className="min-w-0 flex-1 truncate text-slate-400">
                {month.forecast > 0 &&
                  `${formatDecimalDays(month.forecast)} j prévus · `}
                {month.missing > 0
                  ? `${formatDecimalDays(month.missing)} j à déclarer`
                  : !month.isRunning && !month.isValidated
                    ? "à valider"
                    : "à jour"}
              </span>

              {month.isValidated && (
                <span className="flex shrink-0 items-center gap-1 text-emerald-600">
                  <Check className="size-3" aria-hidden />
                  Validé
                </span>
              )}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
