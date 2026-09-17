"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";

import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
import { MissionSelector } from "@/components/atoms/MissionSelector";
import { TeammateSelector } from "@/components/atoms/TeammateSelector";
import { ValidateMonthDialog } from "@/components/atoms/ValidateMonthDialog";
import { TimesheetGrid } from "@/components/organisms/TimesheetGrid";
import { Button } from "@/components/ui/button";
import { formatMonth } from "@/lib/dates";
import { useTimesheetMonth } from "@/lib/use-timesheet-month";

/** Ecran de saisie : la matrice du mois et sa navigation. */
export function TimesheetPage() {
  const mois = useTimesheetMonth();
  const { grid, cursor } = mois;

  const [declarationOuverte, setDeclarationOuverte] = useState(false);
  const [validationOuverte, setValidationOuverte] = useState(false);

  return (
    <main className="mx-auto max-w-[1600px] p-6">
      <header className="mb-6">
        <h1 className="text-lg font-semibold">Activité</h1>
        <p className="text-sm text-slate-500">
          Déclarez votre temps en journées ou demi-journées. Tant que le mois n&apos;est
          pas validé, tout reste modifiable.
        </p>
      </header>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="icon"
            aria-label="Mois précédent"
            onClick={mois.goToPreviousMonth}
          >
            <ChevronLeft />
          </Button>
          <h2 className="min-w-48 text-center text-lg font-semibold capitalize">
            {formatMonth(cursor.year, cursor.month)}
          </h2>
          <Button
            variant="outline"
            size="icon"
            aria-label="Mois suivant"
            onClick={mois.goToNextMonth}
          >
            <ChevronRight />
          </Button>
        </div>

        <div className="flex items-center gap-3">
          <TeammateSelector
            teammates={mois.teammates}
            selectedId={mois.targetUserId}
            onSelect={mois.viewTeammate}
          />

          {grid?.is_writable && (
            <MissionSelector
              projects={mois.projects}
              excludedIds={mois.displayedProjectIds}
              onSelect={mois.addMission}
              onDeclareNew={() => setDeclarationOuverte(true)}
            />
          )}

          {grid?.is_writable && mois.isOwnMonth && (
            <Button onClick={() => setValidationOuverte(true)}>Valider le mois</Button>
          )}
        </div>
      </div>

      {!mois.isOwnMonth && (
        <p className="mb-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Vous consultez le mois d&apos;un collègue. Toute modification sera enregistrée
          à votre nom.
        </p>
      )}

      {grid && !grid.is_writable && (
        <p className="mb-4 rounded-md border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-700">
          Ce mois est validé et ne peut plus être modifié. Seul un manager peut le
          rouvrir.
        </p>
      )}

      {mois.isLoading && <p className="text-muted-foreground text-sm">Chargement…</p>}

      {grid && (
        <TimesheetGrid
          grid={grid}
          extraRows={mois.extraRows}
          today={mois.today}
          onSetValue={mois.setDayValue}
        />
      )}

      <DeclareProjectDialog
        open={declarationOuverte}
        onOpenChange={setDeclarationOuverte}
        onConfirm={mois.declareProject}
      />

      {grid && (
        <ValidateMonthDialog
          open={validationOuverte}
          onOpenChange={setValidationOuverte}
          mois={formatMonth(cursor.year, cursor.month)}
          totalSaisi={grid.total_realise + grid.total_prevu}
          joursOuvres={grid.working_days}
          onConfirm={mois.validate}
        />
      )}
    </main>
  );
}
