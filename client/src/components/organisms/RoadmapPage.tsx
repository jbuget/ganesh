"use client";

import { GroupingSelect } from "@/components/atoms/GroupingSelect";
import { PageHeader } from "@/components/atoms/PageHeader";
import { RoadmapLegend } from "@/components/atoms/RoadmapLegend";
import { RoadmapSummaryBar } from "@/components/atoms/RoadmapSummaryBar";
import { SpanSelect } from "@/components/atoms/SpanSelect";
import { PageLayout } from "@/components/organisms/PageLayout";
import { RoadmapTimeline } from "@/components/organisms/RoadmapTimeline";
import { useRoadmapScreen } from "@/lib/use-roadmap";

/**
 * The portfolio ahead: what was delivered, what is promised, and when.
 *
 * The other half of « Planification », and a different question. The plan
 * asks what fits and who carries it, week by week, over what is left to
 * build; this asks what lands when, over everything, services already running
 * included. The plan is arbitrated by the team; this is shown outside it.
 *
 * Which is why the date the team announced is the subject here and a mere
 * term of a subtraction there — and why this screen is the one place it can
 * be posted.
 */
export function RoadmapPage() {
  const {
    roadmap,
    isLoading,
    hasError,
    months,
    setMonths,
    grouping,
    setGrouping,
    saveFailed,
    setTargetDate,
  } = useRoadmapScreen();

  return (
    <PageLayout
      innerScroll
      header={
        <PageHeader
          title="Feuille de route"
          subtitle="Ce qui a été livré, ce qui est annoncé, et ce que la projection en dit"
          actions={
            <>
              <GroupingSelect value={grouping} onChange={setGrouping} />
              <SpanSelect months={months} onChange={setMonths} />
            </>
          }
        />
      }
    >
      <div className="flex h-full min-h-0 flex-col">
        {roadmap && <RoadmapSummaryBar summary={roadmap.summary} />}

        {saveFailed && (
          <p className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
            La date n&apos;a pas pu être enregistrée. Celles affichées sont bien celles
            que le serveur connaît.
          </p>
        )}

        {isLoading && !roadmap && (
          <p className="py-12 text-center text-sm text-slate-400">Lecture…</p>
        )}

        {hasError && (
          <p className="py-12 text-center text-sm text-red-600">
            La feuille de route n&apos;a pas pu être lue.
          </p>
        )}

        {roadmap && (
          <>
            <div className="min-h-0 flex-1">
              <RoadmapTimeline
                missions={roadmap.missions}
                from={roadmap.from_day}
                to={roadmap.to_day}
                today={roadmap.today}
                grouping={grouping}
                onDate={setTargetDate}
              />
            </div>

            <div className="mt-3 shrink-0">
              <RoadmapLegend />
            </div>
          </>
        )}
      </div>
    </PageLayout>
  );
}
