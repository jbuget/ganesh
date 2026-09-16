"use client";

import { DayCell } from "@/components/atoms/DayCell";
import type { DayValue } from "@/lib/day-value";
import { DayHeader } from "@/components/atoms/DayHeader";
import { DayTotalCell } from "@/components/atoms/DayTotalCell";
import { MissionLabel } from "@/components/atoms/MissionLabel";
import { TotalCell } from "@/components/atoms/TotalCell";
import type { MonthGridResponse, ProjectResponse } from "@/lib/api/generated/model";

interface TimesheetGridProps {
  grid: MonthGridResponse;
  extraRows: ProjectResponse[];
  today: string;
  onSetValue: (projectId: number, jour: string, value: DayValue) => void;
}

interface DisplayRow {
  project_id: number;
  label: string;
  estime_j: number | null;
  values: Record<string, number>;
  total_realise: number;
  total_prevu: number;
  total: number;
  consomme_total_j: number;
}

/**
 * La matrice de saisie : missions en lignes, jours du mois en colonnes.
 *
 * Les lignes ajoutees mais encore vides sont conservees localement : sans cela,
 * une mission choisie disparaitrait tant qu'aucune valeur n'y est saisie.
 */
export function TimesheetGrid({
  grid,
  extraRows,
  today,
  onSetValue,
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
      consomme_total_j: row.consomme_total_j,
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
        consomme_total_j: 0,
      })),
  ].sort((a, b) => a.label.localeCompare(b.label, "fr"));

  const readOnly = !grid.is_writable;
  const totalByDate = new Map(grid.day_totals.map((total) => [total.jour, total]));

  /**
   * Un jour non ouvre se reduit a une bande, sauf s'il porte deja une saisie :
   * une donnee heritee doit rester visible et corrigeable, jamais escamotee.
   */
  const estReduit = (jour: string, isOffDay: boolean) =>
    isOffDay && (totalByDate.get(jour)?.total ?? 0) === 0;

  return (
    <div className="max-w-full overflow-x-auto">
      <table className="w-max border-separate border-spacing-0 border-t border-l border-slate-500 text-slate-800">
        <caption className="sr-only">Temps saisi par mission et par jour</caption>
        <thead>
          <tr>
            <th
              scope="col"
              className="sticky left-0 z-10 h-11 w-56 border-r border-b border-r-slate-500 border-b-slate-300 bg-white px-3 text-left text-xs font-medium text-slate-600"
            >
              <span className="sr-only">Mission</span>
            </th>
            {grid.days.map((day, dayIndex) => (
              <DayHeader
                isNarrow={estReduit(day.jour, day.is_off_day)}
                key={day.jour}
                jour={day.jour}
                isLastDay={dayIndex === grid.days.length - 1}
                isOffDay={day.is_off_day}
                isToday={day.jour === today}
                label={day.label ?? null}
              />
            ))}
            <th
              scope="col"
              className="h-11 w-14 border-r border-b border-r-slate-500 border-b-slate-300 bg-white px-2 text-xs font-medium text-slate-600"
            >
              <span className="sr-only">Total du mois</span>
            </th>
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
                key={day.jour}
                value={totalByDate.get(day.jour)?.total ?? 0}
                isOffDay={day.is_off_day}
                isNarrow={estReduit(day.jour, day.is_off_day)}
                strongSides={
                  dayIndex === grid.days.length - 1 ? ["right", "bottom"] : ["bottom"]
                }
              />
            ))}
            <TotalCell
              value={grid.total_realise + grid.total_prevu}
              isStrong
              strongSides={["right", "bottom"]}
            />
          </tr>
        </thead>

        <tbody>
          {rows.length === 0 && (
            <tr>
              <td
                colSpan={grid.days.length + 2}
                // Seule ligne du corps : elle ferme le tableau en bas et a droite.
                className="border-r border-b border-r-slate-500 border-b-slate-500 bg-white px-3 py-6 text-center text-sm text-slate-500"
              >
                Aucune mission pour ce mois. Ajoutez-en une pour commencer à saisir.
              </td>
            </tr>
          )}
          {rows.map((row, rowIndex) => (
            <tr key={row.project_id}>
              <th
                scope="row"
                className={[
                  "sticky left-0 z-10 w-56 border-r border-b border-r-slate-500 bg-white px-3 py-1.5 text-left text-sm font-normal",
                  rowIndex === rows.length - 1
                    ? "border-b-slate-500"
                    : "border-b-slate-300",
                ].join(" ")}
              >
                <MissionLabel
                  label={row.label}
                  consommeJ={row.consomme_total_j}
                  estimeJ={row.estime_j}
                />
              </th>
              {grid.days.map((day, dayIndex) => (
                <DayCell
                  key={day.jour}
                  isLastDay={dayIndex === grid.days.length - 1}
                  value={(row.values[day.jour] ?? 0) as DayValue}
                  isOffDay={day.is_off_day}
                  isNarrow={estReduit(day.jour, day.is_off_day)}
                  isFuture={day.jour > today}
                  isReadOnly={readOnly}
                  isLastRow={rowIndex === rows.length - 1}
                  label={`${row.label} — ${day.jour}`}
                  onChange={(next) => onSetValue(row.project_id, day.jour, next)}
                />
              ))}
              <TotalCell
                value={row.total}
                isStrong
                strongSides={
                  rowIndex === rows.length - 1 ? ["right", "bottom"] : ["right"]
                }
              />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
