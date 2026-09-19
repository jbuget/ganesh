"use client";

import { Plus, Upload } from "lucide-react";
import { useMemo, useState } from "react";

import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
import { ImportProjectsDialog } from "@/components/atoms/ImportProjectsDialog";
import { PageHeader } from "@/components/atoms/PageHeader";
import { MissionFilters } from "@/components/molecules/MissionFilters";
import { MissionsTable } from "@/components/organisms/MissionsTable";
import { PageLayout } from "@/components/organisms/PageLayout";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { Button } from "@/components/ui/button";
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
 *
 * The page holds the question — the criteria, the order, what to say when
 * nothing comes back — and hands the answer to the table.
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
      {/* Wide enough for ten columns, not so wide as to stretch the names. */}
      <div className="max-w-[1400px]">
        {screen.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {/* An empty list is answered here and not by the table: the reason is
            the page's — a filter that keeps nothing, or a reference list still
            to be filled. */}
        {screen.tree.length === 0 && !screen.isLoading && (
          <p className="py-8 text-center text-sm text-slate-500">
            {hasFilter
              ? "Aucune mission ne répond aux filtres."
              : "Aucun projet. Déclarez-en un ou importez votre référentiel."}
          </p>
        )}

        {screen.tree.length > 0 && (
          <MissionsTable
            tree={screen.tree}
            sorted={sorted}
            onSort={sortBy}
            isExpanded={screen.isExpanded}
            onToggle={screen.toggle}
            now={now}
            onOpen={(projectId) => panel.open(projectId)}
            onOpenThread={(projectId) => panel.open(projectId, "updates")}
          />
        )}
      </div>

      <DeclareProjectDialog
        open={declaring}
        onOpenChange={setDeclaration}
        // A name declares a mission but does not steer it: phase, priority,
        // estimate and people are still to be given. The panel is where they
        // are given, so one is taken there rather than left before a list to
        // search for what one has just created.
        onConfirm={async (label) => {
          const created = await screen.declare(label, "project");
          panel.open(created.id);
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
