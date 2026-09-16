"use client";

import { DayCell, type DayValue } from "@/components/atoms/DayCell";
import { DayHeader } from "@/components/atoms/DayHeader";
import { TotalCell } from "@/components/atoms/TotalCell";
import { MissionSelector } from "@/components/molecules/MissionSelector";
import type { MonthGridResponse, ProjectResponse } from "@/lib/api/generated/model";
import { formatTotal } from "@/lib/dates";

interface TimesheetGridProps {
  grid: MonthGridResponse;
  projects: ProjectResponse[];
  extraRows: ProjectResponse[];
  today: string;
  onSetValue: (projectId: number, jour: string, value: DayValue) => void;
  onAddMission: (projectId: number) => void;
  onDeclareNew: () => void;
}

interface DisplayRow {
  project_id: number;
  label: string;
  estime_j: number | null;
  values: Record<string, number>;
  total_realise: number;
  total_prevu: number;
  total: number;
}

/**
 * La matrice de saisie : missions en lignes, jours du mois en colonnes.
 *
 * Les lignes ajoutees mais encore vides sont conservees localement : sans cela,
 * une mission choisie disparaitrait tant qu'aucune valeur n'y est saisie.
 */
export function TimesheetGrid({
  grid,
  projects,
  extraRows,
  today,
  onSetValue,
  onAddMission,
  onDeclareNew,
}: TimesheetGridProps) {
  const rows: DisplayRow[] = [
    ...grid.rows.map((row) => ({
      project_id: row.project_id,
      label: row.label,
      estime_j: row.estime_j ?? null,
      values: row.values as Record<string, number>,
      total_realise: row.total_realise,
      total_prevu: row.total_prevu,
      total: row.total,
    })),
    ...extraRows
      .filter((p) => !grid.rows.some((row) => row.project_id === p.id))
      .map((p) => ({
        project_id: p.id,
        label: p.label,
        estime_j: p.estime_j ?? null,
        values: {},
        total_realise: 0,
        total_prevu: 0,
        total: 0,
      })),
  ].sort((a, b) => a.label.localeCompare(b.label, "fr"));

  const readOnly = !grid.is_writable;
  const dayByDate = new Map(grid.days.map((day) => [day.jour, day]));
  const totalByDate = new Map(grid.day_totals.map((total) => [total.jour, total]));

  return (
    <div className="w-fit max-w-full overflow-x-auto rounded-lg border border-slate-400">
      <table className="border-collapse text-slate-800">
        <caption className="sr-only">Temps saisi par mission et par jour</caption>
        <thead>
          <tr>
            <th
              scope="col"
              className="sticky left-0 z-10 h-12 w-64 border-r-2 border-b-2 border-r-slate-400 border-b-slate-400 bg-white px-3 text-left text-xs font-medium text-slate-600"
            >
              Mission
            </th>
            {grid.days.map((day) => (
              <DayHeader
                key={day.jour}
                jour={day.jour}
                isOffDay={day.is_off_day}
                isToday={day.jour === today}
                label={day.label ?? null}
              />
            ))}
            <th
              scope="col"
              className="h-12 w-16 border-b-2 border-l-2 border-slate-400 bg-white px-2 text-xs font-medium text-slate-600"
            >
              Total
            </th>
          </tr>
        </thead>

        <tbody>
          {rows.map((row) => (
            <tr key={row.project_id}>
              <th
                scope="row"
                className="sticky left-0 z-10 max-w-64 truncate border-r-2 border-b border-slate-300 border-r-slate-400 bg-white px-3 py-1.5 text-left text-sm font-normal"
                title={row.label}
              >
                {row.label}
                {row.estime_j !== null && (
                  <span className="ml-2 text-xs text-slate-400">
                    {formatTotal(row.total_realise)}/{row.estime_j} j
                  </span>
                )}
              </th>
              {grid.days.map((day) => (
                <DayCell
                  key={day.jour}
                  value={(row.values[day.jour] ?? 0) as DayValue}
                  isOffDay={day.is_off_day}
                  isFuture={day.jour > today}
                  isToday={day.jour === today}
                  isReadOnly={readOnly}
                  label={`${row.label} — ${day.jour}`}
                  onChange={(next) => onSetValue(row.project_id, day.jour, next)}
                />
              ))}
              <TotalCell
                value={row.total}
                isStrong
                className="border-l-2 border-l-slate-400"
              />
            </tr>
          ))}

          {!readOnly && (
            <tr>
              <th
                scope="row"
                className="sticky left-0 z-10 border-r-2 border-b border-slate-300 border-r-slate-400 bg-white px-2 py-1.5 text-left font-normal"
              >
                <MissionSelector
                  projects={projects}
                  excludedIds={rows.map((row) => row.project_id)}
                  onSelect={onAddMission}
                  onDeclareNew={onDeclareNew}
                  disabled={readOnly}
                />
              </th>
              <td
                colSpan={grid.days.length + 1}
                className="border-b border-slate-300 bg-white"
              />
            </tr>
          )}
        </tbody>

        <tfoot className="border-t-2 border-slate-400">
          <tr>
            <th
              scope="row"
              className="sticky left-0 z-10 border-t-2 border-r-2 border-slate-400 bg-slate-100 px-3 py-1.5 text-left text-sm font-medium"
            >
              Total par jour
            </th>
            {grid.days.map((day) => {
              const total = totalByDate.get(day.jour);
              const isOffDay = dayByDate.get(day.jour)?.is_off_day ?? false;
              return (
                <TotalCell
                  key={day.jour}
                  value={total?.total ?? 0}
                  isAlert={
                    total?.exceeds_capacity || (isOffDay && (total?.total ?? 0) > 0)
                  }
                />
              );
            })}
            <TotalCell
              value={grid.total_realise + grid.total_prevu}
              isStrong
              className="border-l-2 border-l-slate-400"
            />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
