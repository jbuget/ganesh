"use client";

import { Trash2 } from "lucide-react";

import { DayCell } from "@/components/atoms/DayCell";
import type { DayValue } from "@/lib/day-value";
import { DayHeader } from "@/components/atoms/DayHeader";
import { DayTotalCell } from "@/components/atoms/DayTotalCell";
import { MissionLabel } from "@/components/atoms/MissionLabel";
import { TotalCell } from "@/components/atoms/TotalCell";
import type { MonthGridResponse } from "@/lib/api/generated/model";

interface TimesheetGridProps {
  grid: MonthGridResponse;
  today: string;
  onSetValue: (
    projectId: number,
    activityId: number | null,
    day: string,
    value: DayValue,
  ) => void;
  /** Mission picker, housed in the last row. Absent when the month is closed. */
  addingMission?: React.ReactNode;
  /** Removing a mission. Absent when the month is closed. */
  onRemoveMission?: (projectId: number, activityId: number | null) => void;
  /**
   * Opening a mission in the side panel. Available whatever the month's state:
   * reading a mission's sheet is not writing on it.
   */
  onOpenMission?: (projectId: number) => void;
}

interface DisplayRow {
  project_id: number;
  activity_id: number | null;
  label: string;
  /** The mission above the row, so two « Développement » never read alike. */
  project_label: string;
  estimated_days: number | null;
  values: Record<string, number>;
  actual_total: number;
  forecast_total: number;
  total: number;
  total_consumed_days: number;
}

/**
 * The entry grid: missions as rows, days of the month as columns.
 *
 * A mission put on the month holds its row with nothing on it: the grid reads
 * what was lined up as much as what was entered.
 */
/** What names a row out loud: the mission, then the trade under it. */
function rowName(row: DisplayRow): string {
  return row.activity_id === null ? row.label : `${row.project_label} — ${row.label}`;
}

export function TimesheetGrid({
  grid,
  today,
  onSetValue,
  addingMission,
  onRemoveMission,
  onOpenMission,
}: TimesheetGridProps) {
  const rows: DisplayRow[] = grid.rows
    .map((row) => ({
      project_id: row.project_id,
      activity_id: row.activity_id ?? null,
      label: row.label,
      project_label: row.project_label,
      estimated_days: row.estimated_days ?? null,
      values: row.values as Record<string, number>,
      actual_total: row.actual_total,
      forecast_total: row.forecast_total,
      total: row.total,
      total_consumed_days: row.total_consumed_days,
    }))
    // Grouped by mission, then by trade: the grid reads as the list of
    // missions one works on, each cut into what one does on it.
    .sort(
      (a, b) =>
        a.project_label.localeCompare(b.project_label, "fr") ||
        a.label.localeCompare(b.label, "fr"),
    );

  const readOnly = !grid.is_writable;
  const totalByDate = new Map(grid.day_totals.map((total) => [total.day, total]));

  /**
   * The add row closes the table when it is there: it then carries the strong
   * bottom rule, and the missions are separated by a light one.
   */
  const closesTheTable = (rowIndex: number) =>
    !addingMission && rowIndex === rows.length - 1;

  /**
   * A non-working day shrinks to a band, unless it already carries an entry:
   * inherited data must stay visible and correctable, never spirited away.
   */
  const isNarrow = (day: string, isOffDay: boolean) =>
    isOffDay && (totalByDate.get(day)?.total ?? 0) === 0;

  return (
    <div className="max-w-full overflow-x-auto">
      <table className="w-max border-separate border-spacing-0 border-l border-slate-500 text-slate-800">
        <caption className="sr-only">Temps saisi par projet et par jour</caption>
        <thead>
          <tr>
            <th
              scope="col"
              className="sticky left-0 z-10 h-11 w-56 border-t border-r border-b border-t-slate-500 border-r-slate-500 border-b-slate-300 bg-white px-3 text-left text-xs font-medium text-slate-600"
            >
              <span className="sr-only">Projet</span>
            </th>
            {grid.days.map((day, dayIndex) => (
              <DayHeader
                isNarrow={isNarrow(day.day, day.is_off_day)}
                key={day.day}
                day={day.day}
                isLastDay={dayIndex === grid.days.length - 1}
                isOffDay={day.is_off_day}
                isToday={day.day === today}
                label={day.label ?? null}
              />
            ))}
            <th
              scope="col"
              className="h-11 w-14 border-t border-r border-b border-t-slate-500 border-r-slate-500 border-b-slate-300 bg-white px-2 text-xs font-medium text-slate-600"
            >
              <span className="sr-only">Total du mois</span>
            </th>
            {onRemoveMission && (
              // Outside the frame: this column carries an action, not data.
              // That is why the top rule is carried by the cells and not by the
              // table, which would have run it all the way here.
              <th scope="col" className="w-10">
                <span className="sr-only">Retirer le projet</span>
              </th>
            )}
          </tr>

          <tr>
            <th
              scope="row"
              className="sticky left-0 z-10 border-r border-b border-r-slate-500 border-b-slate-500 bg-slate-50 px-3 py-1.5 text-left text-sm font-medium"
            >
              Total
              <span className="ml-2 text-xs font-normal text-slate-500">
                ({grid.working_days} jrs. ouvrés)
              </span>
            </th>
            {grid.days.map((day, dayIndex) => (
              <DayTotalCell
                key={day.day}
                value={totalByDate.get(day.day)?.total ?? 0}
                isOffDay={day.is_off_day}
                isNarrow={isNarrow(day.day, day.is_off_day)}
                strongSides={
                  dayIndex === grid.days.length - 1 ? ["right", "bottom"] : ["bottom"]
                }
              />
            ))}
            <TotalCell
              value={grid.actual_total + grid.forecast_total}
              isStrong
              strongSides={["right", "bottom"]}
            />
            {onRemoveMission && <td className="w-10" />}
          </tr>
        </thead>

        <tbody>
          {rows.length === 0 && !addingMission && (
            <tr>
              <td
                colSpan={grid.days.length + 2}
                // The only row in the body: it closes the table at the bottom
                // and on the right.
                className="border-r border-b border-r-slate-500 border-b-slate-500 bg-white px-3 py-6 text-center text-sm text-slate-500"
              >
                {/* A validated month refuses what the invitation offers: it
                    states emptiness instead of asking for a gesture the grid
                    would turn down. */}
                {readOnly
                  ? "Aucun projet n'a été déclaré sur ce mois."
                  : "Aucun projet pour ce mois. Ajoutez-en un pour commencer à saisir."}
              </td>
            </tr>
          )}
          {rows.map((row, rowIndex) => (
            <tr key={`${row.project_id}:${row.activity_id ?? ""}`}>
              <th
                scope="row"
                className={[
                  "sticky left-0 z-10 w-56 border-r border-b border-r-slate-500 bg-white px-3 py-1.5 text-left text-sm font-normal",
                  closesTheTable(rowIndex)
                    ? "border-b-slate-500"
                    : "border-b-slate-300",
                ].join(" ")}
              >
                {/* The name is the way in: from one's month one opens the
                    very same panel the kanban and the reference list open,
                    rather than going looking for the mission elsewhere. */}
                {onOpenMission ? (
                  <button
                    type="button"
                    aria-label={`Ouvrir ${rowName(row)}`}
                    onClick={() => onOpenMission(row.project_id)}
                    className="flex w-full min-w-0 cursor-pointer text-left hover:underline"
                  >
                    <MissionLabel
                      label={row.label}
                      mission={row.project_label}
                      isUnderItsMission={row.activity_id !== null}
                      consumedDays={row.total_consumed_days}
                      estimatedDays={row.estimated_days}
                    />
                  </button>
                ) : (
                  <MissionLabel
                    label={row.label}
                    mission={row.project_label}
                    isUnderItsMission={row.activity_id !== null}
                    consumedDays={row.total_consumed_days}
                    estimatedDays={row.estimated_days}
                  />
                )}
              </th>
              {grid.days.map((day, dayIndex) => (
                <DayCell
                  key={day.day}
                  isLastDay={dayIndex === grid.days.length - 1}
                  value={(row.values[day.day] ?? 0) as DayValue}
                  isOffDay={day.is_off_day}
                  isNarrow={isNarrow(day.day, day.is_off_day)}
                  isFuture={day.day > today}
                  isReadOnly={readOnly}
                  isLastRow={closesTheTable(rowIndex)}
                  // The mission is part of the name: a dozen missions cut
                  // into « Développement » would otherwise give a dozen cells
                  // reading alike to anyone listening rather than looking.
                  label={`${rowName(row)} — ${day.day}`}
                  onChange={(next) =>
                    onSetValue(row.project_id, row.activity_id, day.day, next)
                  }
                />
              ))}
              <TotalCell
                value={row.total}
                isStrong
                strongSides={closesTheTable(rowIndex) ? ["right", "bottom"] : ["right"]}
              />
              {onRemoveMission && (
                <td className="w-10 pl-2 align-middle">
                  <button
                    type="button"
                    aria-label={`Retirer ${rowName(row)}`}
                    onClick={() => onRemoveMission(row.project_id, row.activity_id)}
                    className="cursor-pointer rounded p-1 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
                  >
                    <Trash2 className="size-4" aria-hidden />
                  </button>
                </td>
              )}
            </tr>
          ))}
          {addingMission && (
            <tr>
              <th
                scope="row"
                // Closes the table at the bottom, as the last mission did.
                className="sticky left-0 z-10 w-56 border-r border-b border-r-slate-500 border-b-slate-500 bg-white px-3 py-1.5 text-left font-normal"
              >
                {addingMission}
              </th>
              <td
                colSpan={grid.days.length + 1}
                className="border-r border-b border-r-slate-500 border-b-slate-500 bg-white"
              />
              {onRemoveMission && <td className="w-10" />}
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
