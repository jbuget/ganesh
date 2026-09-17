"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";

import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
import { MissionSelector } from "@/components/atoms/MissionSelector";
import { PageHeader } from "@/components/atoms/PageHeader";
import { PageLayout } from "@/components/organisms/PageLayout";
import { RemoveMissionDialog } from "@/components/atoms/RemoveMissionDialog";
import { TeammateSelector } from "@/components/atoms/TeammateSelector";
import { ValidateMonthDialog } from "@/components/atoms/ValidateMonthDialog";
import { TimesheetGrid } from "@/components/organisms/TimesheetGrid";
import { Button } from "@/components/ui/button";
import { formatMonth } from "@/lib/dates";
import { useTimesheetMonth } from "@/lib/use-timesheet-month";

/** Ecran de saisie : la matrice du mois et sa navigation. */
export function TimesheetPage() {
  const month = useTimesheetMonth();
  const { grid, cursor } = month;

  const [declarationOuverte, setDeclarationOuverte] = useState(false);
  const [validationOuverte, setValidationOuverte] = useState(false);
  const [aRetirer, setARetirer] = useState<{
    id: number;
    label: string;
    total: number;
  } | null>(null);

  /**
   * Une ligne vide s'en va sans ceremonie : il n'y a rien a perdre. Des qu'elle
   * porte du temps, on annonce ce qui sera efface avant de le faire.
   */
  function demanderLeRetrait(projectId: number) {
    const line = grid?.rows.find((row) => row.project_id === projectId);
    if (!line || line.total === 0) {
      void month.removeMission(projectId);
      return;
    }
    setARetirer({ id: projectId, label: line.label, total: line.total });
  }

  return (
    <PageLayout
      entete={
        <PageHeader
          titre="Activité"
          soustitre="Déclarez votre temps en journées ou demi-journées. Tant que le mois n'est pas validé, tout reste modifiable."
        />
      }
    >
      {/*
        Les trois commandes de la matrice, juste au-dessus d'elle : de qui on
        regarde le mois, quel mois, et la seule action qui l'engage. Les deux
        cotes prennent la meme part de l'espace restant, ce qui centre le mois
        quelle que soit la largeur des deux autres.
      */}
      <div className="mb-3 flex flex-wrap items-center gap-4">
        <div className="flex flex-1 justify-start">
          <TeammateSelector
            teammates={month.teammates}
            selectedId={month.targetUserId}
            onSelect={month.viewTeammate}
          />
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="icon"
            aria-label="Mois précédent"
            onClick={month.goToPreviousMonth}
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
            onClick={month.goToNextMonth}
          >
            <ChevronRight />
          </Button>
        </div>

        <div className="flex flex-1 justify-end">
          {grid?.is_writable && month.isOwnMonth && (
            <Button onClick={() => setValidationOuverte(true)}>Valider le mois</Button>
          )}
        </div>
      </div>

      {!month.isOwnMonth && (
        <p className="mb-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Vous consultez le mois d&apos;un collègue. Toute modification sera enregistrée
          à votre name.
        </p>
      )}

      {grid && !grid.is_writable && (
        <p className="mb-4 rounded-md border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-700">
          Ce month est validé et ne peut plus être modifié. Seul un manager peut le
          rouvrir.
        </p>
      )}

      {month.isLoading && <p className="text-muted-foreground text-sm">Chargement…</p>}

      {grid && (
        <TimesheetGrid
          grid={grid}
          extraRows={month.extraRows}
          today={month.today}
          onSetValue={month.setDayValue}
          onRemoveMission={grid.is_writable ? demanderLeRetrait : undefined}
          ajoutDeMission={
            grid.is_writable ? (
              <MissionSelector
                projects={month.projects}
                excludedIds={month.displayedProjectIds}
                onSelect={month.addMission}
                onDeclareNew={() => setDeclarationOuverte(true)}
              />
            ) : null
          }
        />
      )}

      {aRetirer && (
        <RemoveMissionDialog
          open
          onOpenChange={(ouvert) => !ouvert && setARetirer(null)}
          label={aRetirer.label}
          total={aRetirer.total}
          onConfirm={async () => {
            await month.removeMission(aRetirer.id);
            setARetirer(null);
          }}
        />
      )}

      <DeclareProjectDialog
        open={declarationOuverte}
        onOpenChange={setDeclarationOuverte}
        onConfirm={month.declareProject}
      />

      {grid && (
        <ValidateMonthDialog
          open={validationOuverte}
          onOpenChange={setValidationOuverte}
          month={formatMonth(cursor.year, cursor.month)}
          totalSaisi={grid.actual_total + grid.forecast_total}
          joursOuvres={grid.working_days}
          onConfirm={month.validate}
        />
      )}
    </PageLayout>
  );
}
