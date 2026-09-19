"use client";

import {
  PointerSensor,
  pointerWithin,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useRef, useState } from "react";

import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { canBeAttached, canReceive } from "@/lib/mission-attach";
import type { ProjectNode } from "@/lib/project-tree";

/**
 * Dragging a mission onto the project it belongs to, from the first press to
 * the save.
 *
 * Nothing is anticipated on screen: a row that jumped under its new project
 * before the server agreed would have to jump back. What the gesture changes
 * while it lasts is what it shows — the row taken hold of, the row aimed at —
 * and the list is read again once the answer is in.
 *
 * Left without an `onAttach`, the hook hands back a gesture that offers
 * nothing: the table then draws itself as it always has.
 */
export function useMissionDrag(
  tree: ProjectNode[],
  onAttach?: (missionId: number, parentId: number) => void | Promise<void>,
) {
  const [dragged, setDragged] = useState<ProjectListItemResponse | null>(null);
  // A few pixels before the drag starts: a row is clickable in full, and
  // without that margin every click on the handle would begin a gesture.
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  );
  // Letting go over another row ends the gesture with a click, which the
  // browser sends to what the two rows have in common — the table. Without
  // this, every drop opened the mission that had just been moved.
  const dropped = useRef(false);

  /** The mission behind an id, wherever it sits in the tree. */
  function find(id: number): ProjectListItemResponse | null {
    for (const { mission, workPackages } of tree) {
      if (mission.project.id === id) return mission;
      const found = workPackages.find((one) => one.project.id === id);
      if (found) return found;
    }
    return null;
  }

  return {
    /** The mission being carried, and what the copy under the cursor shows. */
    dragged,
    sensors,
    // The row under the cursor, not the one the dragged rectangle happens to
    // overlap: rows are barely taller than a handle, and going by rectangles
    // dropped the mission one line off from where it was aimed.
    collisionDetection: pointerWithin,

    onDragStart(event: DragStartEvent) {
      setDragged(find(Number(event.active.id)));
    },

    onDragEnd(event: DragEndEvent) {
      const mission = dragged;
      setDragged(null);
      dropped.current = true;
      if (!event.over || mission === null) return;
      const target = find(Number(event.over.id));
      if (target === null || !canReceive(target, mission)) return;
      void onAttach?.(mission.project.id, target.project.id);
    },

    onDragCancel() {
      setDragged(null);
    },

    /** What a row may do under the gesture being made, if any. */
    gesture(mission: ProjectListItemResponse, subProjects: number) {
      if (!onAttach) return {};
      return {
        movable: canBeAttached(mission, subProjects),
        receiving: canReceive(mission, dragged),
      };
    },

    /**
     * Swallows the click that closes a drag, on the way down: the capture
     * phase runs before the row's own handler, which therefore never fires.
     */
    onClickCapture(event: { stopPropagation: () => void }) {
      if (!dropped.current) return;
      dropped.current = false;
      event.stopPropagation();
    },

    /**
     * A gesture that ended outside the table left its click there, and the
     * mark would wait to swallow an honest one. Pressing again clears it: the
     * press comes before the click it belongs to.
     */
    onPointerDownCapture() {
      dropped.current = false;
    },
  };
}
