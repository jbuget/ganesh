import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { SortableContext } from "@dnd-kit/sortable";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SortableProjectCard } from "./SortableProjectCard";
import type { BoardCardResponse } from "@/lib/api/generated/model";

/** Frozen reference time: previews do not depend on when the run happens. */
const NOW = new Date("2026-09-16T11:00:00Z");

const card = {
  consumed_days: 5,
  build_days: 5,
  contributors: [],
  comments: 0,
  latest_update: null,
  sub_projects: 0,
  parent: null,
  project: {
    id: 1,
    label: "Portail bailleurs",
    kind: "project",
    status: "development",
    parent_id: null,
    is_active: true,
    is_followed: false,
    estimated_days: 20,
    position: 0,
  },
} as unknown as BoardCardResponse;

/** The board's own sensors: a few pixels tell a drag from a click. */
function Board({ children }: { children: React.ReactNode }) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor),
  );
  return (
    <DndContext sensors={sensors}>
      <SortableContext items={[card.project.id]}>
        <ul>{children}</ul>
      </SortableContext>
    </DndContext>
  );
}

const show = (props: Partial<React.ComponentProps<typeof SortableProjectCard>> = {}) =>
  render(
    <Board>
      <SortableProjectCard card={card} now={NOW} onFollowChange={() => {}} {...props} />
    </Board>,
  );

const theCard = () => screen.getByRole("article");

/** Presses on the card, carries it `distance` pixels down, and lets go. */
function drag(distance: number) {
  const at = { isPrimary: true, button: 0, clientX: 100, clientY: 100 };
  fireEvent.pointerDown(theCard(), at);
  fireEvent.pointerMove(document, { ...at, clientY: 100 + distance });
  fireEvent.pointerUp(document, { ...at, clientY: 100 + distance });
}

describe("SortableProjectCard", () => {
  // @dnd-kit swallows clicks for a moment after a drop: the clock is ours, so
  // that moment ends when a test says so, and never spills into the next one.
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("is grabbed anywhere, so it shows no grip of its own", () => {
    show();

    expect(document.querySelector("svg.lucide-grip-vertical")).toBeNull();
  });

  it("puts the follow mark at the end of the title row", () => {
    show();

    const row = screen.getByRole("heading").parentElement!;
    expect(row.lastElementChild).toBe(
      screen.getByRole("button", { name: "Suivre ce projet" }),
    );
  });

  it("keeps a handle for the keyboard, named after the mission", () => {
    show();

    expect(
      screen.getByRole("button", { name: "Déplacer Portail bailleurs" }),
    ).toBeInTheDocument();
  });

  it("opens the mission on a plain click", () => {
    const onOpen = vi.fn();
    show({ onOpen });

    fireEvent.click(theCard());

    expect(onOpen).toHaveBeenCalledWith(1);
  });

  it("opens the mission when the pointer barely moves", () => {
    const onOpen = vi.fn();
    show({ onOpen });

    drag(3);
    fireEvent.click(theCard());

    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("does not open the mission it was just dropped from", () => {
    // Released near where it was taken, the card receives the click that ends
    // the gesture: a drop is not a request to read the mission.
    const onOpen = vi.fn();
    show({ onOpen });

    drag(40);
    fireEvent.click(theCard());

    expect(onOpen).not.toHaveBeenCalled();
  });

  it("opens the mission again on the next click after a drop", () => {
    const onOpen = vi.fn();
    show({ onOpen });

    drag(40);
    fireEvent.click(theCard());
    vi.advanceTimersByTime(100);
    fireEvent.click(theCard());

    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("neither grabs nor offers a handle to a reader who may not write", () => {
    const onOpen = vi.fn();
    show({ onOpen, readOnly: true });

    expect(screen.queryByRole("button", { name: /Déplacer/ })).toBeNull();
    drag(40);
    fireEvent.click(theCard());
    expect(onOpen).toHaveBeenCalledTimes(1);
  });
});
