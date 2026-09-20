"use client";

import { GroupingSelect } from "@/components/atoms/GroupingSelect";
import { PageHeader } from "@/components/atoms/PageHeader";
import { RoadmapLegend } from "@/components/atoms/RoadmapLegend";
import { RoadmapSummaryBar } from "@/components/atoms/RoadmapSummaryBar";
import { SpanSelect } from "@/components/atoms/SpanSelect";
import { MissionFilters } from "@/components/molecules/MissionFilters";
import { PageLayout } from "@/components/organisms/PageLayout";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { RoadmapTimeline } from "@/components/organisms/RoadmapTimeline";
import { useOpenedMission } from "@/lib/opened-mission";
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
    filters,
    hasFilter,
    setFilters,
    clearFilters,
    criteria,
    saveFailed,
    setTargetDate,
    refresh,
  } = useRoadmapScreen();

  const panel = useOpenedMission();

  return (
    <PageLayout
      innerScroll
      header={
        <PageHeader
          title="Feuille de route"
          subtitle="Ce qui a été livré, ce qui est annoncé, et ce que la projection en dit"
        />
      }
    >
      <div className="flex h-full min-h-0 flex-col">
        {/* The window and the grouping sit at the far end of the filter bar,
            where the reference list puts its choice of columns: they settle
            how the drawing is read, next to what it is narrowed to, and not
            among the page's title. */}
        <MissionFilters
          filters={filters}
          hasFilter={hasFilter}
          onChange={setFilters}
          onClear={clearFilters}
          criteria={criteria}
          trailing={
            <>
              <GroupingSelect value={grouping} onChange={setGrouping} />
              <SpanSelect months={months} onChange={setMonths} />
            </>
          }
        />

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
                onOpen={(projectId) => panel.open(projectId)}
                onDate={setTargetDate}
              />
            </div>

            <div className="mt-3 shrink-0">
              <RoadmapLegend />
            </div>
          </>
        )}
      </div>

      {panel.openedMission && (
        <ProjectPanel
          // The tab is part of the key: reopening the same mission on its
          // thread must remount the panel, which picks its tab on opening.
          key={`${panel.openedMission}:${panel.openTab ?? ""}`}
          projectId={panel.openedMission}
          tab={panel.openTab}
          onClose={panel.close}
          // A phase changed in the panel moves a segment out here, and an
          // estimate given lands a bar that was not there: the drawing is
          // read again rather than left saying what was true a moment ago.
          onMissionChanged={refresh}
          onOpenMission={(projectId) => panel.open(projectId)}
        />
      )}
    </PageLayout>
  );
}
