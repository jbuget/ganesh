"use client";

import {
  useLayoutEffect,
  useRef,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

/** Offset of the tooltip from the cursor, so as not to hide it. */
const OFFSET = { x: 14, y: 18 };

/** The breathing room left between the bubble and the window edge. */
const MARGE = 8;

interface State {
  x: number;
  y: number;
  content: ReactNode;
}

/**
 * The bubble itself, folded back into the window.
 *
 * Placed as is at the cursor, a tall or wide bubble would run off the screen at
 * the bottom or the right — all the more since it does not scroll. It is
 * therefore measured before paint to bring it back inside the window:
 * `useLayoutEffect` runs between render and display, so the correction never
 * shows.
 */
function Bubble({
  x,
  y,
  rich,
  children,
}: State & { rich: boolean; children: ReactNode }) {
  const element = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ left: x + OFFSET.x, top: y + OFFSET.y });

  useLayoutEffect(() => {
    if (!element.current) return;
    const { width, height } = element.current.getBoundingClientRect();

    // To the right and below the cursor by default; on the other side when
    // there is no room left, and against the edge if it fits nowhere.
    const left =
      x + OFFSET.x + width > window.innerWidth - MARGE
        ? Math.max(MARGE, x - OFFSET.x - width)
        : x + OFFSET.x;
    const top =
      y + OFFSET.y + height > window.innerHeight - MARGE
        ? Math.max(MARGE, window.innerHeight - MARGE - height)
        : y + OFFSET.y;

    setPosition({ left, top });
  }, [x, y]);

  return (
    <div
      ref={element}
      role="tooltip"
      style={position}
      className={
        rich
          ? "pointer-events-none fixed z-50 max-w-md rounded-lg border border-slate-200 bg-white px-3 py-2.5 shadow-xl"
          : "pointer-events-none fixed z-50 rounded-md bg-slate-800 px-2.5 py-1.5 text-xs whitespace-nowrap text-white shadow-lg"
      }
    >
      {children}
    </div>
  );
}

/**
 * A tooltip that appears at the cursor.
 *
 * It appears on hover, where the browser's native tooltip keeps one waiting a
 * second, and it is mounted in a portal on `body`: rendered inside a `sticky`
 * cell, which carries its own stacking context, it slipped under the next
 * row's cell and got clipped.
 *
 * The content is given on hover and not at the call: one tooltip thus serves
 * several neighbouring elements, such as contributor avatars.
 *
 * `rich` turns it from the dark banner of a name into a light card, where
 * formatted content renders as it is written. It freezes there on first
 * appearance rather than following the cursor: a paragraph being read must not
 * move before one's eyes.
 */
export function useCursorTooltip({ rich = false }: { rich?: boolean } = {}) {
  const [state, setState] = useState<State | null>(null);

  const tooltip = state
    ? createPortal(
        <Bubble key={`${state.x},${state.y}`} {...state} rich={rich}>
          {state.content}
        </Bubble>,
        document.body,
      )
    : null;

  return {
    tooltip,
    follow: (event: MouseEvent, content: ReactNode) => {
      const position = { x: event.clientX, y: event.clientY, content };
      setState((previous) => (rich && previous ? previous : position));
    },
    leave: () => setState(null),
  };
}
