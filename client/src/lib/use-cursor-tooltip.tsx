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
 * Infobulle qui parait au curseur.
 *
 * Elle parait des le survol, la ou l'infobulle native du navigateur se fait
 * attendre une seconde, et elle est montee dans un portail sur `body` : rendue
 * a l'interieur d'une cellule `sticky`, qui porte son propre contexte
 * d'empilement, elle passait sous la cellule de la ligne suivante et se
 * trouvait rognee.
 *
 * Le contenu est donne au survol et non a l'appel : une meme infobulle sert
 * ainsi plusieurs elements voisins, comme les pastilles d'intervenants.
 *
 * `riche` la fait passer du bandeau sombre d'un nom a une carte claire, ou du
 * contenu mis en forme se rend tel qu'il s'ecrit. Elle s'y fige a la premiere
 * apparition plutot que de suivre le curseur : un paragraphe qu'on lit ne doit
 * pas bouger sous les yeux.
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
      setState((precedent) => (rich && precedent ? precedent : position));
    },
    leave: () => setState(null),
  };
}
