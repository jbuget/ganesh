"use client";

import { Search } from "lucide-react";
import { useEffect, useRef } from "react";

import { CommandPaletteRow } from "@/components/atoms/CommandPaletteRow";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import {
  closePalette,
  openPalette,
  usePaletteShortcut,
} from "@/lib/command-palette-store";
import { useCommandPalette } from "@/lib/use-command-palette";

/**
 * Where one goes, without leaving the keyboard.
 *
 * It navigates and nothing else: every line is a place, and opening one from
 * here leaves exactly the trace that clicking it would have. Writing from a
 * palette is another feature, and one that would have to say out loud what the
 * screens say by refusing.
 *
 * It sits in the frame rather than on a screen, since it is reached from every
 * one of them. What it knows and what it does live in `useCommandPalette`;
 * here there is the drawing, and the keys that stand for its gestures.
 */
export function CommandPalette() {
  usePaletteShortcut();
  const palette = useCommandPalette();
  // Read at each draw rather than frozen at mount: the palette lives in the
  // frame, which outlasts a working day, and « hier » would go on being said.
  const now = new Date();
  const list = useRef<HTMLDivElement>(null);

  // Keeping the selection in sight is a matter of drawing, not of knowing
  // where it stands: the hook moves it, this follows it with the scrollbar.
  useEffect(() => {
    list.current
      ?.querySelector('[data-active="true"]')
      ?.scrollIntoView({ block: "nearest" });
  }, [palette.selection]);

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    const gesture: Record<string, () => void> = {
      ArrowDown: () => palette.moveBy(1),
      ArrowUp: () => palette.moveBy(-1),
      Enter: () => palette.go(palette.found[palette.selection]),
    };
    const asked = gesture[event.key];
    if (!asked) return;

    event.preventDefault();
    asked();
  }

  return (
    <Dialog
      open={palette.open}
      onOpenChange={(next) => (next ? openPalette() : closePalette())}
    >
      {/* Higher than the middle of the page: the list grows downwards, and a
          palette that grew from the centre would push its own field about. */}
      <DialogContent
        showCloseButton={false}
        className="top-[15%] max-h-[70vh] translate-y-0 gap-0 overflow-hidden p-0 sm:max-w-xl"
      >
        <DialogTitle className="sr-only">Rechercher</DialogTitle>

        <div className="flex items-center gap-2 border-b border-slate-200 px-3 py-2.5">
          <Search className="size-4 shrink-0 text-slate-400" aria-hidden />
          <input
            type="text"
            autoFocus
            role="combobox"
            aria-expanded
            aria-controls="command-palette-results"
            aria-activedescendant={palette.found[palette.selection]?.key}
            aria-label="Rechercher un projet, une personne ou un écran"
            placeholder="Rechercher un projet, une personne ou un écran…"
            value={palette.query}
            onChange={(event) => palette.ask(event.target.value)}
            onKeyDown={onKeyDown}
            className="min-w-0 flex-1 bg-transparent text-sm focus:outline-none"
          />
        </div>

        {palette.found.length === 0 ? (
          <p className="px-3 py-8 text-center text-sm text-slate-400">
            Rien ne correspond à cette recherche.
          </p>
        ) : (
          <div
            id="command-palette-results"
            ref={list}
            role="listbox"
            aria-label="Résultats"
            className="max-h-[52vh] overflow-y-auto p-1.5"
          >
            {palette.sections.map((section) => (
              <div key={section.group} role="group" aria-label={section.label}>
                <p
                  aria-hidden
                  className="px-2 pt-2 pb-1 text-xs font-medium tracking-wide text-slate-400"
                >
                  {section.label}
                </p>
                <ul>
                  {section.items.map((destination) => (
                    <CommandPaletteRow
                      key={destination.key}
                      destination={destination}
                      selected={destination === palette.found[palette.selection]}
                      now={now}
                      onOpen={() => palette.go(destination)}
                      onHover={() => palette.select(palette.found.indexOf(destination))}
                    />
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
