"use client";

import { Trash2 } from "lucide-react";

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
  onSetValue: (projectId: number, day: string, value: DayValue) => void;
  /** Selecteur de mission, loge dans la derniere ligne. Absent si le mois est clos. */
  ajoutDeMission?: React.ReactNode;
  /** Retrait d'une mission. Absent si le mois est clos. */
  onRemoveMission?: (projectId: number) => void;
}

interface DisplayRow {
  project_id: number;
  label: string;
  estimated_days: number | null;
  values: Record<string, number>;
  actual_total: number;
  forecast_total: number;
  total: number;
  total_consumed_days: number;
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
  ajoutDeMission,
  onRemoveMission,
}: TimesheetGridProps) {
  const rows: DisplayRow[] = [
    ...grid.rows.map((row) => ({
      project_id: row.project_id,
      label: row.label,
      estimated_days: row.estimated_days ?? null,
      values: row.values as Record<string, number>,
      actual_total: row.actual_total,
      forecast_total: row.forecast_total,
      total: row.total,
      total_consumed_days: row.total_consumed_days,
    })),
    ...extraRows
      .filter((p) => !grid.rows.some((row) => row.project_id === p.id))
      .map((p) => ({
        project_id: p.id,
        label: p.label,
        estimated_days: p.estimated_days ?? null,
        values: {},
        actual_total: 0,
        forecast_total: 0,
        total: 0,
        total_consumed_days: 0,
      })),
  ].sort((a, b) => a.label.localeCompare(b.label, "fr"));

  const readOnly = !grid.is_writable;
  const totalByDate = new Map(grid.day_totals.map((total) => [total.day, total]));

  /**
   * La ligne d'ajout ferme le tableau quand elle est la : c'est elle qui porte
   * alors le trait fort du bas, et les missions se separent d'un trait faible.
   */
  const fermeLeTableau = (rowIndex: number) =>
    !ajoutDeMission && rowIndex === rows.length - 1;

  /**
   * Un jour non ouvre se reduit a une bande, sauf s'il porte deja une saisie :
   * une donnee heritee doit rester visible et corrigeable, jamais escamotee.
   */
  const estReduit = (day: string, isOffDay: boolean) =>
    isOffDay && (totalByDate.get(day)?.total ?? 0) === 0;

  return (
    <div className="max-w-full overflow-x-auto">
      <table className="w-max border-separate border-spacing-0 border-l border-slate-500 text-slate-800">
        <caption className="sr-only">Temps saisi par mission et par jour</caption>
        <thead>
          <tr>
            <th
              scope="col"
              className="sticky left-0 z-10 h-11 w-56 border-t border-r border-b border-t-slate-500 border-r-slate-500 border-b-slate-300 bg-white px-3 text-left text-xs font-medium text-slate-600"
            >
              <span className="sr-only">Mission</span>
            </th>
            {grid.days.map((day, dayIndex) => (
              <DayHeader
                isNarrow={estReduit(day.day, day.is_off_day)}
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
              // Hors du cadre : cette colonne porte une action, pas une donnee.
              // C'est pourquoi le trait du haut est porte par les cellules et
              // non par la table, qui l'aurait prolonge jusqu'ici.
              <th scope="col" className="w-10">
                <span className="sr-only">Retirer la mission</span>
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
                isNarrow={estReduit(day.day, day.is_off_day)}
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
          {rows.length === 0 && !ajoutDeMission && (
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
                  fermeLeTableau(rowIndex)
                    ? "border-b-slate-500"
                    : "border-b-slate-300",
                ].join(" ")}
              >
                <MissionLabel
                  label={row.label}
                  consommeJ={row.total_consumed_days}
                  estimeJ={row.estimated_days}
                />
              </th>
              {grid.days.map((day, dayIndex) => (
                <DayCell
                  key={day.day}
                  isLastDay={dayIndex === grid.days.length - 1}
                  value={(row.values[day.day] ?? 0) as DayValue}
                  isOffDay={day.is_off_day}
                  isNarrow={estReduit(day.day, day.is_off_day)}
                  isFuture={day.day > today}
                  isReadOnly={readOnly}
                  isLastRow={fermeLeTableau(rowIndex)}
                  label={`${row.label} — ${day.day}`}
                  onChange={(next) => onSetValue(row.project_id, day.day, next)}
                />
              ))}
              <TotalCell
                value={row.total}
                isStrong
                strongSides={fermeLeTableau(rowIndex) ? ["right", "bottom"] : ["right"]}
              />
              {onRemoveMission && (
                <td className="w-10 pl-2 align-middle">
                  <button
                    type="button"
                    aria-label={`Retirer ${row.label}`}
                    onClick={() => onRemoveMission(row.project_id)}
                    className="cursor-pointer rounded p-1 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
                  >
                    <Trash2 className="size-4" aria-hidden />
                  </button>
                </td>
              )}
            </tr>
          ))}
          {ajoutDeMission && (
            <tr>
              <th
                scope="row"
                // Ferme le tableau en bas, comme le faisait la derniere mission.
                className="sticky left-0 z-10 w-56 border-r border-b border-r-slate-500 border-b-slate-500 bg-white px-3 py-1.5 text-left font-normal"
              >
                {ajoutDeMission}
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
