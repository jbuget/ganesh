"use client";

import { GroupingSelect } from "@/components/atoms/GroupingSelect";
import { PageHeader } from "@/components/atoms/PageHeader";
import { RoadmapLegend } from "@/components/atoms/RoadmapLegend";
import { RoadmapSummaryBar } from "@/components/atoms/RoadmapSummaryBar";
import { YearSelect } from "@/components/atoms/YearSelect";
import { PageLayout } from "@/components/organisms/PageLayout";
import { RoadmapTimeline } from "@/components/organisms/RoadmapTimeline";
import { useRoadmapScreen } from "@/lib/use-roadmap";

/**
 * The portfolio over a year: what was delivered, what is promised, and when.
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
    year,
    setYear,
    grouping,
    setGrouping,
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
              <YearSelect year={year} onChange={setYear} />
            </>
          }
        />
      }
    >
      {roadmap && <RoadmapSummaryBar summary={roadmap.summary} />}

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
          <RoadmapTimeline
            missions={roadmap.missions}
            from={roadmap.from_day}
            to={roadmap.to_day}
            today={roadmap.today}
            grouping={grouping}
            onDate={setTargetDate}
          />

          <div className="mt-3">
            <RoadmapLegend />
          </div>
        </>
      )}
    </PageLayout>
  );
}
