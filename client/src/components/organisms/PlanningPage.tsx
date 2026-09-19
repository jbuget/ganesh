"use client";

import { RotateCcw } from "lucide-react";
import { useState } from "react";

import { HorizonSelect } from "@/components/atoms/HorizonSelect";
import { PageHeader } from "@/components/atoms/PageHeader";
import { CapacityTimeline } from "@/components/organisms/CapacityTimeline";
import { PageLayout } from "@/components/organisms/PageLayout";
import { WorkloadTimeline } from "@/components/organisms/WorkloadTimeline";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatShortDate } from "@/lib/dates";
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
    isError,
    horizonMonths,
    setHorizon,
    move,
    isHypothesis,
    reset,
  } = useWorkloadPlanScreen();
  const [tab, setTab] = useState("missions");

  const weeks = plan?.weeks ?? [];

  return (
    <PageLayout
      innerScroll
      header={
        <PageHeader
          title="Planification"
          subtitle={
            plan
              ? `Du ${formatShortDate(plan.from_day)} au ${formatShortDate(plan.to_day)}, sur les disponibilités déclarées`
              : "Projection du reste à faire sur les disponibilités déclarées"
          }
          actions={
            <>
              {isHypothesis && (
                <Button
                  variant="outline"
                  size="sm"
                  className="cursor-pointer"
                  onClick={reset}
                >
                  <RotateCcw className="size-4" />
                  Revenir à l&apos;ordre de l&apos;équipe
                </Button>
              )}
              <HorizonSelect months={horizonMonths} onChange={setHorizon} />
            </>
          }
        />
      }
    >
      {isHypothesis && (
        <p className="mb-3 rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-900">
          Hypothèse en cours : cet ordre n&apos;est pas enregistré. Pour le rendre réel,
          déplacez la carte sur le kanban ou changez sa priorité.
        </p>
      )}

      <Tabs value={tab} onValueChange={setTab} className="flex min-h-0 flex-col">
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

        {isError && (
          <p className="py-12 text-center text-sm text-red-600">
            La projection n&apos;a pas pu être calculée.
          </p>
        )}

        {plan && (
          <>
            <TabsContent value="missions" className="min-h-0 flex-1 overflow-auto">
              <WorkloadTimeline missions={missions} weeks={weeks} onMove={move} />
            </TabsContent>

            <TabsContent value="people" className="min-h-0 flex-1 overflow-auto">
              <CapacityTimeline people={plan.people} weeks={weeks} />
            </TabsContent>
          </>
        )}
      </Tabs>
    </PageLayout>
  );
}
