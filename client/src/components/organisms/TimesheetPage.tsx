"use client";

import { ChevronLeft, ChevronRight, History } from "lucide-react";
import { useState } from "react";

import { AssignedMissionsCallout } from "@/components/atoms/AssignedMissionsCallout";
import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
import { MissionSelector } from "@/components/atoms/MissionSelector";
import { MonthAuditDialog } from "@/components/organisms/MonthAuditDialog";
import { PageHeader } from "@/components/atoms/PageHeader";
import { PageLayout } from "@/components/organisms/PageLayout";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { RemoveMissionDialog } from "@/components/atoms/RemoveMissionDialog";
import { ReopenMonthDialog } from "@/components/atoms/ReopenMonthDialog";
import { TeammateSelector } from "@/components/atoms/TeammateSelector";
import { ValidateMonthDialog } from "@/components/atoms/ValidateMonthDialog";
import { TimesheetGrid } from "@/components/organisms/TimesheetGrid";
import { Button } from "@/components/ui/button";
import { formatMonth } from "@/lib/dates";
import { useOpenedMission } from "@/lib/opened-mission";
import { useTimesheetMonth } from "@/lib/use-timesheet-month";

/** Entry screen: the month grid and its navigation. */
export function TimesheetPage() {
  const month = useTimesheetMonth();
  const { grid, cursor } = month;
  // The same panel as the kanban and the reference list, held by the same
  // address: a mission opened from one's month is shared by a link, and going
  // back closes it.
  const panel = useOpenedMission();

  const [declareOpen, setDeclareOpen] = useState(false);
  const [validateOpen, setValidateOpen] = useState(false);
  const [reopenOpen, setReopenOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [toRemove, setToRemove] = useState<{
    id: number;
    label: string;
    total: number;
  } | null>(null);

  /**
   * An empty row goes without ceremony: there is nothing to lose. As soon as it
   * carries time, what will be erased is announced before it happens.
   */
  function askToRemove(projectId: number) {
    const line = grid?.rows.find((row) => row.project_id === projectId);
    if (!line || line.total === 0) {
      void month.removeMission(projectId);
      return;
    }
    setToRemove({ id: projectId, label: line.label, total: line.total });
  }

  return (
    <PageLayout
      header={
        <PageHeader
          title="Saisie des temps"
          subtitle="Où est passé votre temps ce mois-ci, et ce qu'il reste à déclarer."
          actions={
            <TeammateSelector
              teammates={month.teammates}
              selectedId={month.targetUserId}
              onSelect={month.viewTeammate}
            />
          }
        />
      }
    >
      {/* Before the month it speaks of: what the team put one on is read first,
          and the reminder never passes for a row of the grid. */}
      {month.writable && (
        <AssignedMissionsCallout
          missions={month.missionsToDeclare.map((mission) => ({
            id: mission.id,
            label: mission.label,
          }))}
          onAdd={(projectId) => void month.addMission(projectId)}
        />
      )}

      {/*
        Right above the grid: the month it shows, centred on it, and the gesture
        that commits that month, on its right. Validation does not act on the
        screen but on the month one is looking at — it is what the chevrons
        change, and it reads beside them rather than in the page header, which
        carries what holds from one month to the next. Whose month it is stays
        up there: that is a context, not a gesture on the month.

        A grid rather than a row: the action is a validation, a reopening, or
        nothing at all, and the month must not shift as one walks from one
        month to the next. The three columns hold it in place whatever the
        right-hand one carries.
      */}
      <div className="mb-3 grid grid-cols-[1fr_auto_1fr] items-center">
        <div className="col-start-2 flex items-center gap-3">
          <Button
            variant="outline"
            size="icon"
            className="cursor-pointer"
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
            className="cursor-pointer"
            aria-label="Mois suivant"
            onClick={month.goToNextMonth}
          >
            <ChevronRight />
          </Button>
        </div>

        <div className="col-start-3 flex items-center justify-end gap-2">
          {/* Reading the month's life next to the gesture that commits it, and
              a shade lighter: one opens a window, the other locks the month.
              Always offered — how a month got here is worth reading whether or
              not it is still open. */}
          <Button
            variant="ghost"
            className="cursor-pointer"
            onClick={() => setHistoryOpen(true)}
          >
            <History />
            Historique
          </Button>

          {month.canValidate && (
            <Button className="cursor-pointer" onClick={() => setValidateOpen(true)}>
              Valider le mois
            </Button>
          )}

          {/* Giving a month back to entry is a step backwards, not the outcome
              of the month: it does not carry the primary weight the validation
              does. */}
          {month.canReopen && (
            <Button
              variant="outline"
              className="cursor-pointer"
              onClick={() => setReopenOpen(true)}
            >
              Rouvrir le mois
            </Button>
          )}
        </div>
      </div>

      {!month.isOwnMonth && (
        <p className="mb-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Vous consultez le mois d&apos;un collègue. Toute modification sera enregistrée
          à votre nom.
        </p>
      )}

      {/* Whoever can undo the lock is not told that someone else must: the
          sentence follows what the reader can actually do about it. */}
      {grid && !grid.is_writable && (
        <p className="mb-4 rounded-md border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-700">
          {month.canReopen
            ? "Ce mois est validé et n'accepte plus de saisie. Rouvrez-le pour le modifier."
            : "Ce mois est validé et ne peut plus être modifié. Seul un manager peut le rouvrir."}
        </p>
      )}

      {month.isLoading && <p className="text-muted-foreground text-sm">Chargement…</p>}

      {grid && (
        <TimesheetGrid
          grid={grid}
          readOnly={!month.writable}
          today={month.today}
          onSetValue={month.setDayValue}
          onRemoveMission={month.writable ? askToRemove : undefined}
          onOpenMission={(projectId) => panel.open(projectId)}
          addingMission={
            month.writable ? (
              <MissionSelector
                projects={month.projects}
                excludedIds={month.displayedProjectIds}
                assignedIds={month.assignedIds}
                onSelect={(projectId) => void month.addMission(projectId)}
                onDeclareNew={() => setDeclareOpen(true)}
              />
            ) : null
          }
        />
      )}

      {toRemove && (
        <RemoveMissionDialog
          open
          onOpenChange={(isOpen) => !isOpen && setToRemove(null)}
          label={toRemove.label}
          total={toRemove.total}
          onConfirm={async () => {
            await month.removeMission(toRemove.id);
            setToRemove(null);
          }}
        />
      )}

      <DeclareProjectDialog
        open={declareOpen}
        onOpenChange={setDeclareOpen}
        onConfirm={month.declareProject}
      />

      {panel.openedMission && (
        <ProjectPanel
          // The tab is part of the key: reopening the same mission on its
          // thread must remount the panel, which picks its tab on opening.
          key={`${panel.openedMission}:${panel.openTab ?? ""}`}
          projectId={panel.openedMission}
          tab={panel.openTab}
          onClose={panel.close}
          // A mission renamed or re-estimated in the panel must read the same
          // in the grid behind it.
          onMissionChanged={month.refresh}
          onOpenMission={(projectId) => panel.open(projectId)}
        />
      )}

      {/* Mounted with the window rather than with the page: the log is read
          when somebody asks for it, and read afresh every time — reopening it
          after an entry must show that entry. */}
      {historyOpen && (
        <MonthAuditDialog
          open
          onOpenChange={setHistoryOpen}
          month={month.month}
          label={formatMonth(cursor.year, cursor.month)}
          userId={month.targetUserId}
          teammate={month.viewedTeammateName}
        />
      )}

      <ReopenMonthDialog
        open={reopenOpen}
        onOpenChange={setReopenOpen}
        month={formatMonth(cursor.year, cursor.month)}
        teammate={month.viewedTeammateName}
        onConfirm={month.reopen}
      />

      {grid && (
        <ValidateMonthDialog
          open={validateOpen}
          onOpenChange={setValidateOpen}
          month={formatMonth(cursor.year, cursor.month)}
          totalEntered={grid.actual_total + grid.forecast_total}
          workingDays={grid.working_days}
          onConfirm={month.validate}
        />
      )}
    </PageLayout>
  );
}
