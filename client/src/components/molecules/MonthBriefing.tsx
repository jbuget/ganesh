"use client";

import { CalendarClock, CalendarX2, CheckCircle2, UserRoundCheck } from "lucide-react";
import Link from "next/link";

import { TodoItem } from "@/components/atoms/TodoItem";
import type { MonthCursor } from "@/lib/dates";
import { formatDecimalDays, formatMonth, monthParam } from "@/lib/dates";
import type { OpenMonth } from "@/lib/home";

interface MonthBriefingProps {
  cursor: MonthCursor;
  actualDays: number;
  forecastDays: number;
  workingDays: number;
  /** The months gone by still open, the closest one first. */
  monthsToSettle: OpenMonth[];
  /** Working days already past with nothing on them. */
  daysMissing: string[];
  /** Missions one contributes to with nothing declared this month. */
  missionsToDeclare: { id: number; label: string }[];
}

/**
 * Where one's month stands, and what is left to do on it.
 *
 * The month names the panel rather than the word « À faire »: a reminder
 * without its month says nothing, and the figure above the list is what makes
 * the reminders readable — « il manque 3 jours » reads differently at 4 days
 * declared and at 19.
 *
 * Nothing is written from here. Each line names its gap and hands over to the
 * screen that closes it: the home screen tells, the grid does.
 */
export function MonthBriefing({
  cursor,
  actualDays,
  forecastDays,
  workingDays,
  monthsToSettle,
  daysMissing,
  missionsToDeclare,
}: MonthBriefingProps) {
  // Over-declaring is possible — the day total is a warning, not a block — so
  // the shares are capped: the bar must not run past its frame.
  const share = (days: number) =>
    workingDays ? Math.min((days / workingDays) * 100, 100) : 0;
  const delivered = share(actualDays);
  const planned = share(actualDays + forecastDays) - delivered;
  const nothingToDo =
    monthsToSettle.length === 0 &&
    daysMissing.length === 0 &&
    missionsToDeclare.length === 0;

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-4">
      <header className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-base font-semibold capitalize">
          {formatMonth(cursor.year, cursor.month)}
        </h2>
        <p className="text-sm text-slate-500 tabular-nums">
          <span className="font-medium text-slate-900">
            {formatDecimalDays(actualDays)} j
          </span>{" "}
          réalisés
          {forecastDays > 0 &&
            ` · ${formatDecimalDays(forecastDays)} j prévus`} sur {workingDays} jours
          ouvrés
        </p>
      </header>

      {/* The bar says at a glance how full the month is; the figures above say
          exactly how full. Forecast is set back from delivered, as in the grid
          totals: what is planned must never read as done. */}
      <div
        className="mt-2.5 flex h-1.5 overflow-hidden rounded-full bg-slate-200"
        role="presentation"
      >
        <div className="bg-slate-700" style={{ width: `${delivered}%` }} />
        <div className="bg-slate-300" style={{ width: `${planned}%` }} />
      </div>

      {nothingToDo ? (
        <p className="mt-3 flex items-center gap-2 text-sm text-slate-500">
          <CheckCircle2 className="size-4 shrink-0 text-emerald-500" aria-hidden />
          Tout est à jour. Rien ne vous attend.
        </p>
      ) : (
        <ul className="mt-2 divide-y divide-slate-100">
          {/* One line per month left behind, the closest first. A month never
              filled in and a month filled in but never closed are two different
              gestures, so each is named by the one it calls for. */}
          {monthsToSettle.map((gone) => (
            <TodoItem
              key={monthParam(gone)}
              icon={gone.isEmpty ? CalendarX2 : CalendarClock}
              action={
                <Link
                  href={`/timesheet?month=${monthParam(gone)}`}
                  className="cursor-pointer text-sm font-medium text-sky-700 hover:underline"
                >
                  {gone.isEmpty ? "Saisir" : "Valider"}
                </Link>
              }
            >
              <span className="capitalize">{formatMonth(gone.year, gone.month)}</span>{" "}
              {gone.isEmpty ? "n'a aucun temps saisi." : "n'est pas encore validé."}
            </TodoItem>
          ))}

          {daysMissing.length > 0 && (
            <TodoItem
              icon={CalendarX2}
              action={
                <Link
                  href="/timesheet"
                  className="cursor-pointer text-sm font-medium text-sky-700 hover:underline"
                >
                  Compléter
                </Link>
              }
            >
              {daysMissing.length > 1
                ? `${daysMissing.length} jours ouvrés déjà passés sont sans saisie.`
                : "1 jour ouvré déjà passé est sans saisie."}
            </TodoItem>
          )}

          {missionsToDeclare.length > 0 && (
            <TodoItem
              icon={UserRoundCheck}
              action={
                <Link
                  href="/timesheet"
                  className="cursor-pointer text-sm font-medium text-sky-700 hover:underline"
                >
                  Déclarer
                </Link>
              }
            >
              Vous intervenez sur{" "}
              {missionsToDeclare.map((mission, rank) => (
                <span key={mission.id}>
                  {rank > 0 && (rank === missionsToDeclare.length - 1 ? " et " : ", ")}
                  <span className="font-medium text-slate-900">{mission.label}</span>
                </span>
              ))}{" "}
              sans y avoir saisi de temps.
            </TodoItem>
          )}
        </ul>
      )}
    </section>
  );
}
