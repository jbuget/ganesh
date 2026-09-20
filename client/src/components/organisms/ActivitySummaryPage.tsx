"use client";

import { CoverageNote } from "@/components/atoms/CoverageNote";
import { PageHeader } from "@/components/atoms/PageHeader";
import { RangeSelect } from "@/components/atoms/RangeSelect";
import { ActivityContributors } from "@/components/organisms/ActivityContributors";
import { ActivityMatrix } from "@/components/organisms/ActivityMatrix";
import { PageLayout } from "@/components/organisms/PageLayout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ACTIVITY_RANGES, comparedWith } from "@/lib/activity";
import { summarise } from "@/lib/statistics";
import { useActivityScreen, type ActivityView } from "@/lib/use-activity-summary";

/**
 * Qui a fait quoi, et sur quoi le temps est parti.
 *
 * Rétrospective and factual, where Planification is prospective and arbitrated:
 * nothing here is placed or supposed, everything was declared. A window still
 * running stops today — what comes after it is a forecast, and forecasts are
 * read on Planification.
 *
 * The coverage opens the screen rather than closing it, and that placement is
 * the whole point: read against a coverage of 60 %, every figure below it is a
 * costly fiction.
 */
export function ActivitySummaryPage() {
  const { range, setRange, view, setView, summary, isLoading } = useActivityScreen();

  const header = (
    <PageHeader
      title="Synthèse d'activité"
      subtitle={
        summary
          ? summarise(summary.period)
          : "Qui a fait quoi, et sur quoi le temps est parti"
      }
      actions={
        <RangeSelect value={range} onChange={setRange} ranges={ACTIVITY_RANGES} />
      }
    />
  );

  if (!summary) {
    return (
      <PageLayout header={header}>
        <p className="text-sm text-slate-500">
          {isLoading ? "Chargement de la synthèse…" : "Synthèse indisponible."}
        </p>
      </PageLayout>
    );
  }

  const against = comparedWith(range);
  const silent = summary.contributors
    .filter((someone) => someone.declared_days === 0)
    .map((someone) => someone.display_name);

  return (
    <PageLayout header={header}>
      <div className="flex flex-col gap-6 pb-4">
        <CoverageNote
          coverage={summary.coverage}
          declaredDays={summary.declared_days}
          expectedDays={summary.expected_days}
          silent={silent}
        />

        <Tabs value={view} onValueChange={(next) => setView(next as ActivityView)}>
          <TabsList>
            <TabsTrigger value="project" className="cursor-pointer">
              Par projet
            </TabsTrigger>
            <TabsTrigger value="person" className="cursor-pointer">
              Par personne
            </TabsTrigger>
          </TabsList>

          <TabsContent value="project" className="mt-4 flex flex-col gap-6">
            <ActivityMatrix
              title="Projets"
              lines={summary.projects}
              contributors={summary.contributors}
              totalDays={summary.project_days}
              against={against}
              empty="Aucun temps déclaré sur un projet pour cette période."
            />
            <ActivityMatrix
              title="Hors projet"
              lines={summary.off_project}
              contributors={summary.contributors}
              totalDays={summary.off_project_days}
              against={against}
              empty="Aucun temps hors projet déclaré pour cette période."
            />
          </TabsContent>

          <TabsContent value="person" className="mt-4">
            <ActivityContributors
              contributors={summary.contributors}
              summary={summary}
            />
          </TabsContent>
        </Tabs>
      </div>
    </PageLayout>
  );
}
