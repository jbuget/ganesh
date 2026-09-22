"use client";

import { useState } from "react";

import { HorizonSelect } from "@/components/atoms/HorizonSelect";
import { LeaveWithoutSavingDialog } from "@/components/atoms/LeaveWithoutSavingDialog";
import { PageHeader } from "@/components/atoms/PageHeader";
import { PlanSummaryBar } from "@/components/atoms/PlanSummaryBar";
import { SimulationBar } from "@/components/molecules/SimulationBar";
import { CapacityTimeline } from "@/components/organisms/CapacityTimeline";
import { PageLayout } from "@/components/organisms/PageLayout";
import { WorkloadTimeline } from "@/components/organisms/WorkloadTimeline";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatShortDate } from "@/lib/dates";
import { scenarioNotice } from "@/lib/planning";
import { useUnsavedChangesGuard } from "@/lib/use-unsaved-changes-guard";
import { useWorkloadPlanScreen } from "@/lib/use-workload-plan";

/**
 * The workload plan: what lands when, and who carries it.
 *
 * Two readings of one projection. « Projets » says what lands late; « Personnes »
 * says why. Moving a mission re-asks the whole thing, which is the point of the
 * screen — one arbitrates by trying, and nothing is written until someone
 * decides to change the board itself.
 *
 * The plan is only worth the forecasts it reads. Leave nobody declared is room
 * the projection will happily fill, which is why the subtitle says out loud
 * what it stands on.
 */
export function PlanningPage() {
  const {
    plan,
    missions,
    isLoading,
    hasError,
    horizonMonths,
    setHorizon,
    move,
    moveToTop,
    moveUp,
    moveDown,
    staff,
    isHypothesis,
    reset,
    simulations,
    opened,
    saveError,
    hasUnsavedChanges,
    hasWorkToLose,
    open,
    saveAs,
    saveOver,
    remove,
  } = useWorkloadPlanScreen();
  const [tab, setTab] = useState("missions");

  const guard = useUnsavedChangesGuard(hasWorkToLose);

  const weeks = plan?.weeks ?? [];

  return (
    <PageLayout
      innerScroll
      header={
        <PageHeader
          title="Planification"
          subtitle={
            plan
              ? `Du ${formatShortDate(plan.from_day)} au ${formatShortDate(plan.to_day)} · 4,5 j planifiables par personne et par semaine`
              : "Ce qui tient dans les semaines à venir, et qui le porte."
          }
          actions={
            <>
              <SimulationBar
                simulations={simulations}
                opened={opened}
                isHypothesis={isHypothesis}
                hasUnsavedChanges={hasUnsavedChanges}
                saveError={saveError}
                onOpen={guard.guard(open)}
                onSaveAs={saveAs}
                onSaveOver={saveOver}
                onDelete={remove}
                onReset={reset}
              />
              <HorizonSelect months={horizonMonths} onChange={setHorizon} />
            </>
          }
        />
      }
    >
      {/* The screen arranges its own scrolling, so the height has to travel
          all the way down: without a column holding it, the tab panel would
          have no room to be `flex-1` of, and its `overflow-auto` nothing to
          scroll — the timeline simply ran off the bottom, clipped. */}
      <div className="flex h-full min-h-0 flex-col">
        {isHypothesis && (
          <p className="mb-3 rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-900">
            {scenarioNotice(opened?.name ?? null, hasUnsavedChanges)}
          </p>
        )}

        {plan && <PlanSummaryBar summary={plan.summary} />}

        <LeaveWithoutSavingDialog
          open={guard.isBlocking}
          onOpenChange={(next) => {
            if (!next) guard.stay();
          }}
          simulationName={opened?.name ?? null}
          onDiscard={guard.discard}
        />

        <Tabs
          value={tab}
          onValueChange={setTab}
          className="flex min-h-0 flex-1 flex-col"
        >
          <TabsList className="shrink-0">
            <TabsTrigger value="missions" className="cursor-pointer">
              Projets
            </TabsTrigger>
            <TabsTrigger value="people" className="cursor-pointer">
              Personnes
            </TabsTrigger>
          </TabsList>

          {isLoading && (
            <p className="py-12 text-center text-sm text-slate-400">Calcul…</p>
          )}

          {hasError && (
            <p className="py-12 text-center text-sm text-red-600">
              La projection n&apos;a pas pu être calculée.
            </p>
          )}

          {plan && (
            <>
              {/* The panel gives the height; the scrolling belongs to the timeline,
                  which carries the frame that closes it. */}
              <TabsContent value="missions" className="min-h-0 flex-1">
                <WorkloadTimeline
                  missions={missions}
                  weeks={weeks}
                  team={plan.people.map((person) => person.user)}
                  onMove={move}
                  onTop={moveToTop}
                  onUp={moveUp}
                  onDown={moveDown}
                  onStaff={staff}
                />
              </TabsContent>

              <TabsContent value="people" className="min-h-0 flex-1">
                <CapacityTimeline people={plan.people} weeks={weeks} />
              </TabsContent>
            </>
          )}
        </Tabs>
      </div>
    </PageLayout>
  );
}
