"use client";

import {
  DndContext,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  closestCorners,
  pointerWithin,
  rectIntersection,
  useSensor,
  useSensors,
  type Collision,
  type CollisionDetection,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { useMemo } from "react";

import { PageHeader } from "@/components/atoms/PageHeader";
import { PageLayout } from "@/components/organisms/PageLayout";
import { BoardColumn } from "@/components/molecules/BoardColumn";
import { MissionFilters } from "@/components/molecules/MissionFilters";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { ProjectCard } from "@/components/molecules/ProjectCard";
import { PHASES } from "@/lib/board";
import { filterMissions, inclutLesArchivees } from "@/lib/mission-filters";
import { useBoard } from "@/lib/use-board";
import { useBoardDrag } from "@/lib/use-board-drag";
import { useMissionFilters } from "@/lib/use-mission-filters";
import { useOpenedMission } from "@/lib/opened-mission";

/**
 * A hovered card wins over the column containing it.
 *
 * Both sit under the cursor, and the column alone only says the phase being
 * entered: without this preference, every card landed at the bottom of the
 * column, wherever one was aiming.
 */
const prioritiseCards = (collisions: Collision[]) => {
  const cards = collisions.filter(({ id }) => typeof id === "number");
  return cards.length > 0 ? cards : collisions;
};

/**
 * What actually lies under the cursor, first and foremost.
 *
 * `closestCorners` alone aimed at the neighbouring card rather than the hovered
 * column: dropping into an empty column sent the card to the one next door.
 */
const collisionDetection: CollisionDetection = (args) => {
  const underCursor = pointerWithin(args);
  if (underCursor.length > 0) return prioritiseCards(underCursor);

  const overlap = rectIntersection(args);
  if (overlap.length > 0) return prioritiseCards(overlap);
  return closestCorners(args);
};

/** Mission kanban, one column per phase. */
export function BoardPage() {
  const { filters, hasFilter, set, clear } = useMissionFilters();

  // The scope asked of the server follows the filter: archived missions only
  // arrive when called for, and the board reloads itself as soon as that
  // choice changes.
  const board = useBoard(inclutLesArchivees(filters));
  const drag = useBoardDrag(board);

  // One reference time for the whole board: « il y a 3 h » must not
  // depend on when each card renders.
  const maintenant = useMemo(() => new Date(), []);

  // The open mission lives in the URL: a panel is shared by a link, and going
  // back closes it, as one expects of a screen of its own.
  const panel = useOpenedMission();

  // The six phases stay shown in every case, even empty: the board keeps its
  // shape from one filter to the next, and a column with no card reads as an
  // answer, not as a disappearance.
  //
  // The columns are computed once: the bar's count and each column's must
  // speak of the same cards.
  const visibleColumns = PHASES.map(({ status }) => ({
    status,
    cards: filterMissions(board.columns?.[status] ?? [], filters),
  }));

  const visible = visibleColumns.reduce((total, c) => total + c.cards.length, 0);
  const total = PHASES.reduce(
    (somme, { status }) => somme + (board.columns?.[status]?.length ?? 0),
    0,
  );

  const sensors = useSensors(
    // A few pixels before grabbing: without this, a plain click would start a
    // drag.
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  // The board takes the full width, unlike the other screens: six columns side
  // by side gain from every pixel, and a centred margin would throttle them
  // without helping anyone read.
  return (
    <PageLayout
      defilementInterne
      entete={
        <PageHeader
          title="Kanban"
          subtitle={
            // Under a filter, the list shown is no longer the list arranged: a
            // drop would aim at a rank that does not exist. The cards freeze,
            // and the header says why rather than leaving one to wonder.
            hasFilter
              ? "Tableau filtré : les cartes ne se déplacent plus. Effacez les filtres pour les réorganiser."
              : "Glissez une mission pour changer sa phase ou la réordonner. L'ordre choisi est conservé."
          }
        />
      }
    >
      <div className="flex h-full flex-col">
        <MissionFilters
          filters={filters}
          hasFilter={hasFilter}
          onChange={set}
          onEffacer={clear}
          visible={visible}
          total={total}
        />

        {board.hasError && (
          <p className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
            Le déplacement n&apos;a pas pu être enregistré. Le tableau a été rechargé.
          </p>
        )}

        {!board.columns ? (
          <p className="text-sm text-slate-500">Chargement…</p>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={collisionDetection}
            onDragStart={drag.onDragStart}
            onDragOver={drag.onDragOver}
            onDragEnd={drag.onDragEnd}
            onDragCancel={drag.onDragCancel}
          >
            <div className="flex min-h-0 flex-1 gap-4 overflow-x-auto pb-4">
              {visibleColumns.map(({ status, cards }) => (
                <BoardColumn
                  key={status}
                  status={status}
                  cards={cards}
                  maintenant={maintenant}
                  onIntervenantsChange={board.reload}
                  onOpen={panel.open}
                  frozen={hasFilter}
                />
              ))}
            </div>

            {/*
              The copy following the cursor, slightly tilted and lifted.

              No return animation: it aims at the original element, which has
              changed place or column in the meantime, and used to leave a ghost
              card showing permanently.
            */}
            <DragOverlay dropAnimation={null}>
              {drag.isDragging && (
                <div className="w-64 rotate-2 scale-[1.02] cursor-grabbing">
                  <ProjectCard
                    card={drag.isDragging}
                    maintenant={maintenant}
                    isDragging
                  />
                </div>
              )}
            </DragOverlay>
          </DndContext>
        )}
      </div>

      {panel.openedMission && (
        <ProjectPanel
          key={panel.openedMission}
          projectId={panel.openedMission}
          onClose={panel.close}
          onMissionChanged={board.reload}
        />
      )}
    </PageLayout>
  );
}
