"use client";

import { MissionSelector } from "@/components/atoms/MissionSelector";
import { TimesheetGrid } from "@/components/organisms/TimesheetGrid";
import { formatMonth, formatTotal } from "@/lib/dates";
import { useTimesheetMonth } from "@/lib/use-timesheet-month";

/** Ecran de saisie : la matrice du mois et sa navigation. */
export function TimesheetPage() {
  const mois = useTimesheetMonth();
  const { grid, cursor } = mois;

  async function declareProject() {
    const label = window.prompt("Nom du nouveau projet ?");
    if (!label?.trim()) return;
    await mois.declareProject(label.trim());
  }

  async function validate() {
    const total = (grid?.total_realise ?? 0) + (grid?.total_prevu ?? 0);
    const confirme = window.confirm(
      `Valider ${formatMonth(cursor.year, cursor.month)} ?\n\n` +
        `Total saisi : ${formatTotal(total)} jour(s)\n` +
        `Jours ouvrés : ${grid?.working_days ?? 0}\n\n` +
        "Après validation, vous ne pourrez plus modifier ce mois.\n" +
        "Seul un manager pourra le rouvrir.",
    );
    if (confirme) await mois.validate();
  }

  return (
    <main className="mx-auto max-w-[1600px] p-6">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Mois précédent"
            className="cursor-pointer rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50"
            onClick={mois.goToPreviousMonth}
          >
            ←
          </button>
          <h1 className="min-w-48 text-center text-lg font-semibold capitalize">
            {formatMonth(cursor.year, cursor.month)}
          </h1>
          <button
            type="button"
            aria-label="Mois suivant"
            className="cursor-pointer rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50"
            onClick={mois.goToNextMonth}
          >
            →
          </button>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-slate-500" htmlFor="teammate">
            Collaborateur
          </label>
          <select
            id="teammate"
            className="cursor-pointer rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
            value={mois.targetUserId ?? ""}
            onChange={(event) => mois.viewTeammate(Number(event.target.value))}
          >
            {mois.teammates.map((user) => (
              <option key={user.id} value={user.id}>
                {user.display_name}
              </option>
            ))}
          </select>

          {grid?.is_writable && (
            <MissionSelector
              projects={mois.projects}
              excludedIds={mois.displayedProjectIds}
              onSelect={mois.addMission}
              onDeclareNew={declareProject}
              disabled={false}
            />
          )}

          {grid?.is_writable && mois.isOwnMonth && (
            <button
              type="button"
              className="cursor-pointer rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
              onClick={validate}
            >
              Valider le mois
            </button>
          )}
        </div>
      </header>

      {!mois.isOwnMonth && (
        <p className="mb-4 rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Vous consultez le mois d&apos;un collègue. Toute modification sera enregistrée
          à votre nom.
        </p>
      )}

      {grid && !grid.is_writable && (
        <p className="mb-4 rounded border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-700">
          Ce mois est validé et ne peut plus être modifié. Seul un manager peut le
          rouvrir.
        </p>
      )}

      {mois.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

      {grid && (
        <TimesheetGrid
          grid={grid}
          extraRows={mois.extraRows}
          today={mois.today}
          onSetValue={mois.setDayValue}
        />
      )}
    </main>
  );
}
