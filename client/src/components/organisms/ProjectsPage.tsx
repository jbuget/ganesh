"use client";

import { Plus, Upload } from "lucide-react";
import { Fragment, useMemo, useState } from "react";

import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
import { ImportProjectsDialog } from "@/components/atoms/ImportProjectsDialog";
import { PageHeader } from "@/components/atoms/PageHeader";
import { SortableColumnHeader } from "@/components/atoms/SortableColumnHeader";
import { MissionFilters } from "@/components/molecules/MissionFilters";
import { MissionRow } from "@/components/molecules/MissionRow";
import { PageLayout } from "@/components/organisms/PageLayout";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  CATEGORY_COLUMN,
  DAYS_COLUMN,
  LEFT_MARGIN,
  MEMBERS_COLUMN,
  MISSIONS_TABLE,
  NAME_COLUMN,
  PHASE_COLUMN,
  PRIORITY_COLUMN,
  SEPARATOR,
  THREAD_COLUMN,
} from "@/lib/mission-columns";
import { useOpenedMission } from "@/lib/opened-mission";
import { useMissionFilters } from "@/lib/use-mission-filters";
import { useMissionSort } from "@/lib/use-mission-sort";
import { useProjectsScreen } from "@/lib/use-projects";

/**
 * The mission reference list.
 *
 * The columns say at a glance where each mission stands, what it weighs and who
 * looks after it — what one comes here to compare. They do not edit: a row
 * still opens one thing only, the mission panel, the very same one the kanban
 * opens. A list that edited in place would multiply the paths to the same data,
 * and make them drift apart.
 */
export function ProjectsPage() {
  // The same criteria as the kanban, held by the same address: one filters from
  // one screen, opens the other, and the question asked stays the same.
  const { filters, hasFilter, set, clear } = useMissionFilters();
  // Ordering follows the same path as the filters: the address carries it, and
  // the screen hook renders the tree already in the order asked for.
  const { sorted, toggle: sortBy } = useMissionSort();
  const screen = useProjectsScreen(filters, sorted);
  // One reference time for every row: « il y a 3 h » must not depend
  // on when each one renders.
  const now = useMemo(() => new Date(), []);
  const panel = useOpenedMission();
  const [declaring, setDeclaration] = useState(false);
  const [importing, setImporting] = useState(false);

  return (
    <PageLayout
      header={
        <>
          <PageHeader
            title="Projets"
            subtitle="Gestion des projets et sous-projets"
            actions={
              <>
                {screen.isManager && (
                  <Button variant="outline" onClick={() => setImporting(true)}>
                    <Upload />
                    Importer
                  </Button>
                )}
                <Button onClick={() => setDeclaration(true)}>
                  <Plus />
                  Déclarer un projet
                </Button>
              </>
            }
          />

          {/* With the header, outside the scrolling area: the question asked of
              the reference list must stay readable and editable, whether one
              has gone fifty rows down or off to the right after a column. */}
          <MissionFilters
            filters={filters}
            hasFilter={hasFilter}
            onChange={set}
            onClear={clear}
            visible={screen.visible}
            total={screen.total}
          />
        </>
      }
    >
      {/* Wide enough for nine columns, not so wide as to stretch the names. */}
      <div className="max-w-[1300px]">
        {screen.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {screen.tree.length === 0 && !screen.isLoading && (
          <p className="py-8 text-center text-sm text-slate-500">
            {hasFilter
              ? "Aucune mission ne répond aux filtres."
              : "Aucun projet. Déclarez-en un ou importez votre référentiel."}
          </p>
        )}

        {screen.tree.length > 0 && (
          // The shadcn container opens a scrolling context that would hold the
          // header inside the table: we neutralise it so the `sticky` latches
          // onto the page's scrolling area.
          // The box sizes itself on the table rather than on the available
          // room: the padding of the scrolling area does not count towards what
          // it can travel, and without that band on the right the last column
          // would butt against the window edge.
          <div className="w-max pr-6 [&_[data-slot=table-container]]:overflow-visible">
            <Table className={MISSIONS_TABLE}>
              {/* Sixty rows pass under the header: without it, one no longer
                  knows which column one is reading by the time one reaches the
                  bottom. The background sits on the cells and not on the row:
                  in a table, a row's background paints under the lines that
                  scroll. */}
              <TableHeader className="sticky top-0 z-10 [&_th]:border-b [&_th]:border-slate-200 [&_th]:bg-slate-50">
                <TableRow>
                  <SortableColumnHeader
                    column="project"
                    label="Projet"
                    sorted={sorted}
                    onToggle={sortBy}
                    className={`${NAME_COLUMN} ${LEFT_MARGIN}`}
                  />
                  {/* The follow-up thread: its icon carries the meaning, not a title. */}
                  {/* Only the right-hand line reaches into the header: it marks
                      where the pinned part stops, over the full height of the
                      table. The left-hand one separates two columns, and so
                      starts below their titles. */}
                  <TableHead className={`${THREAD_COLUMN} ${SEPARATOR}`} />
                  <SortableColumnHeader
                    column="phase"
                    label="Phase"
                    sorted={sorted}
                    onToggle={sortBy}
                    className={PHASE_COLUMN}
                  />
                  <SortableColumnHeader
                    column="priority"
                    label="Priorité"
                    sorted={sorted}
                    onToggle={sortBy}
                    className={PRIORITY_COLUMN}
                  />
                  <SortableColumnHeader
                    column="category"
                    label="Catégorie"
                    sorted={sorted}
                    onToggle={sortBy}
                    className={CATEGORY_COLUMN}
                  />
                  {/* Build against its estimate, run apart: the two answer
                      different questions, and a single column carrying both
                      would no longer sort. */}
                  <SortableColumnHeader
                    column="build"
                    label="Build"
                    sorted={sorted}
                    onToggle={sortBy}
                    alignRight
                    className={DAYS_COLUMN}
                  />
                  <SortableColumnHeader
                    column="run"
                    label="Run"
                    sorted={sorted}
                    onToggle={sortBy}
                    alignRight
                    className={DAYS_COLUMN}
                  />
                  {/* Who looks after it does not sort: a column of badges has no
                      order the reader would have in mind. */}
                  <TableHead className={MEMBERS_COLUMN}>Référents</TableHead>
                  <TableHead>Intervenants</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {screen.tree.map(({ mission, workPackages }) => {
                  const expanded = screen.isExpanded(mission.project.id);

                  return (
                    <Fragment key={mission.project.id}>
                      <MissionRow
                        mission={mission}
                        isWorkPackage={mission.project.kind === "work_package"}
                        workPackages={workPackages.length}
                        expanded={expanded}
                        onToggle={() => screen.toggle(mission.project.id)}
                        now={now}
                        onOpen={() => panel.open(mission.project.id)}
                        onOpenThread={() => panel.open(mission.project.id, "updates")}
                      />
                      {expanded &&
                        workPackages.map((workPackage) => (
                          <MissionRow
                            key={workPackage.project.id}
                            mission={workPackage}
                            isWorkPackage
                            now={now}
                            onOpen={() => panel.open(workPackage.project.id)}
                            onOpenThread={() =>
                              panel.open(workPackage.project.id, "updates")
                            }
                          />
                        ))}
                    </Fragment>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}

        {screen.activities.length > 0 && (
          <section className="mt-8">
            <h2 className="mb-2 text-sm font-medium text-slate-600">
              Activités hors projet
            </h2>
            <p className="mb-3 text-sm text-slate-500">
              Elles n&apos;ont ni phase ni estimé, et ne remontent jamais dans Monday.
              Sans elles, les jours ouvrés se reporteraient sur les projets.
            </p>
            <ul className="flex flex-wrap gap-2">
              {screen.activities.map((activity) => (
                <li
                  key={activity.project.id}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
                >
                  {activity.project.label}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <DeclareProjectDialog
        open={declaring}
        onOpenChange={setDeclaration}
        onConfirm={async (label) => {
          await screen.declare(label, "project");
        }}
      />

      <ImportProjectsDialog
        open={importing}
        onOpenChange={setImporting}
        onImport={screen.importCsv}
      />

      {panel.openedMission && (
        <ProjectPanel
          // The tab is part of the key: reopening the same mission on its
          // thread must remount the panel, which picks its tab on opening.
          key={`${panel.openedMission}:${panel.openTab ?? ""}`}
          projectId={panel.openedMission}
          tab={panel.openTab}
          onClose={panel.close}
          onMissionChanged={screen.refresh}
        />
      )}
    </PageLayout>
  );
}
