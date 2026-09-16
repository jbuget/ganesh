"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { DayValue } from "@/components/atoms/DayCell";
import { MissionSelector } from "@/components/molecules/MissionSelector";
import { TimesheetGrid } from "@/components/organisms/TimesheetGrid";
import { setEntry } from "@/lib/api/generated/entries/entries";
import type { ProjectResponse } from "@/lib/api/generated/model";
import { useValidateMonth } from "@/lib/api/generated/months/months";
import { useCreateProject } from "@/lib/api/generated/projects/projects";
import {
  mutationResult,
  useCurrentUser,
  useMonthGrid,
  useProjects,
  useTeammates,
} from "@/lib/api/queries";
import {
  firstDayOfMonth,
  formatMonth,
  formatTotal,
  nextMonth,
  previousMonth,
} from "@/lib/dates";

/** Date du jour en heure locale : `toISOString` renverrait la veille en soiree. */
function todayIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

/** Ecran de saisie : la matrice du mois et sa navigation. */
export function TimesheetPage() {
  const today = todayIso();
  const [cursor, setCursor] = useState(() => ({
    year: Number(today.slice(0, 4)),
    month: Number(today.slice(5, 7)),
  }));
  const [viewedUserId, setViewedUserId] = useState<number | null>(null);
  const [extraRows, setExtraRows] = useState<ProjectResponse[]>([]);

  const queryClient = useQueryClient();
  const mois = firstDayOfMonth(cursor.year, cursor.month);

  const { user: me } = useCurrentUser();
  const { teammates } = useTeammates();
  const { projects } = useProjects();
  const createProject = useCreateProject();
  const validateMonth = useValidateMonth();

  const targetUserId = viewedUserId ?? me?.id ?? null;
  const gridQuery = useMonthGrid(mois, viewedUserId, Boolean(me?.id));
  const grid = gridQuery.grid;
  const isOwnMonth = viewedUserId === null || viewedUserId === me?.id;

  const displayedProjectIds = [
    ...(grid?.rows.map((row) => row.project_id) ?? []),
    ...extraRows.map((project) => project.id),
  ];

  async function refresh() {
    await queryClient.invalidateQueries();
  }

  async function handleSetValue(projectId: number, jour: string, value: DayValue) {
    if (value === 0) return; // La suppression arrive avec l'endpoint DELETE.
    await setEntry(
      { project_id: projectId, jour, valeur: value },
      viewedUserId ? { user_id: viewedUserId } : undefined,
    );
    await refresh();
  }

  async function handleDeclareNew() {
    const label = window.prompt("Nom du nouveau projet ?");
    if (!label?.trim()) return;
    const created = await createProject.mutateAsync({
      data: { label: label.trim(), kind: "projet", statut: "exploration" },
    });
    const project = mutationResult<ProjectResponse>(created);
    setExtraRows((rows) => [...rows, project]);
    await refresh();
  }

  async function handleValidate() {
    const confirmed = window.confirm(
      `Valider ${formatMonth(cursor.year, cursor.month)} ?\n\n` +
        `Total saisi : ${formatTotal(
          (grid?.total_realise ?? 0) + (grid?.total_prevu ?? 0),
        )} jour(s)\n` +
        `Jours ouvrés : ${grid?.working_days ?? 0}\n\n` +
        "Après validation, vous ne pourrez plus modifier ce mois.\n" +
        "Seul un manager pourra le rouvrir.",
    );
    if (!confirmed) return;
    await validateMonth.mutateAsync({ mois });
    await refresh();
  }

  function goToMonth(next: { year: number; month: number }) {
    setCursor(next);
    setExtraRows([]);
  }

  return (
    <main className="mx-auto max-w-[1600px] p-6">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Mois précédent"
            className="cursor-pointer rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50"
            onClick={() => goToMonth(previousMonth(cursor.year, cursor.month))}
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
            onClick={() => goToMonth(nextMonth(cursor.year, cursor.month))}
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
            value={targetUserId ?? ""}
            onChange={(event) => {
              const id = Number(event.target.value);
              setViewedUserId(id === me?.id ? null : id);
            }}
          >
            {teammates.map((user) => (
              <option key={user.id} value={user.id}>
                {user.display_name}
              </option>
            ))}
          </select>

          {grid?.is_writable && (
            <MissionSelector
              projects={projects}
              excludedIds={displayedProjectIds}
              onSelect={(projectId) => {
                const project = projects.find((p) => p.id === projectId);
                if (project) setExtraRows((rows) => [...rows, project]);
              }}
              onDeclareNew={handleDeclareNew}
              disabled={false}
            />
          )}

          {grid?.is_writable && isOwnMonth && (
            <button
              type="button"
              className="cursor-pointer rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
              onClick={handleValidate}
            >
              Valider le mois
            </button>
          )}
        </div>
      </header>

      {!isOwnMonth && (
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

      {gridQuery.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

      {grid && (
        <>
          <TimesheetGrid
            grid={grid}
            extraRows={extraRows}
            today={today}
            onSetValue={handleSetValue}
          />

          <dl className="mt-4 flex flex-wrap gap-8 text-sm">
            <div>
              <dt className="text-slate-500">Réalisé</dt>
              <dd className="text-lg font-semibold">
                {formatTotal(grid.total_realise)} j
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Prévisionnel</dt>
              <dd className="text-lg font-semibold">
                {formatTotal(grid.total_prevu)} j
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Jours ouvrés du mois</dt>
              <dd className="text-lg font-semibold">{grid.working_days} j</dd>
            </div>
          </dl>
        </>
      )}
    </main>
  );
}
