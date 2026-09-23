"use client";

import { useMemo, useState } from "react";

import { useProjects, useTeammates, useTouchedProjects } from "@/lib/api/queries";
import {
  destinations,
  grouped,
  matching,
  TOUCHED_ASKED_FOR,
  type Destination,
  type Section,
} from "@/lib/command-palette";
import { closePalette, usePaletteOpen } from "@/lib/command-palette-store";
import { useGoTo } from "@/lib/url-state";

/** What the palette knows, and what it can be asked to do. */
export interface CommandPalette {
  open: boolean;
  query: string;
  ask: (query: string) => void;
  sections: Section[];
  /** The results in the order they are drawn, which the selection travels. */
  found: Destination[];
  /**
   * Where the selection stands, as an index into `found`. Not named
   * « current »: React reads that property as a ref wherever it appears.
   */
  selection: number;
  /** Puts the selection somewhere, by arrow or under the mouse. */
  select: (index: number) => void;
  /** Walks the selection, wrapping round at either end. */
  moveBy: (step: number) => void;
  /** Goes where a destination leads, and closes behind it. */
  go: (destination: Destination | undefined) => void;
}

/**
 * Everything the palette does, apart from being drawn.
 *
 * The three lists it searches are only asked for once it has been opened: it
 * sits in the frame of every screen, and would otherwise cost three requests
 * a page for something nobody had opened.
 */
export function useCommandPalette(): CommandPalette {
  const open = usePaletteOpen();
  const goTo = useGoTo();

  // Archived projects included: the palette is the only place one is reached
  // without first going to a screen and undoing a filter.
  const { missions } = useProjects(true, open);
  const { teammates } = useTeammates(false, open);
  // What the register saw move, which no mission carries the date of.
  const { touched } = useTouchedProjects(TOUCHED_ASKED_FOR, open);

  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);

  const all = useMemo(
    () => destinations({ missions, teammates, touched }),
    [missions, teammates, touched],
  );
  const sections = useMemo(() => grouped(matching(all, query)), [all, query]);
  // The sections read one after the other give back the ranked order: that is
  // the line the selection travels along, and what it must match on screen.
  const found = useMemo(() => sections.flatMap((section) => section.items), [sections]);
  const selection = Math.min(active, Math.max(found.length - 1, 0));

  // Every opening starts afresh: a palette reopening on the last search would
  // answer a question nobody is asking any more. Adjusted while rendering
  // rather than in an effect, which would draw the old search for a frame.
  const [wasOpen, setWasOpen] = useState(open);
  if (open !== wasOpen) {
    setWasOpen(open);
    if (open) {
      setQuery("");
      setActive(0);
    }
  }

  return {
    open,
    query,
    ask(asked: string) {
      setQuery(asked);
      // A new search is answered from its first line, wherever the selection
      // had wandered on the last one.
      setActive(0);
    },
    sections,
    found,
    selection,
    select: setActive,
    moveBy(step: number) {
      if (found.length === 0) return;
      setActive((index) => (index + step + found.length) % found.length);
    },
    go(destination: Destination | undefined) {
      if (!destination) return;
      closePalette();
      goTo(destination.href);
    },
  };
}
