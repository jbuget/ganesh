"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useProjects, useTeammates } from "@/lib/api/queries";
import { phaseDot, phaseLabel } from "@/lib/board";
import {
  destinations,
  grouped,
  matching,
  type Destination,
} from "@/lib/command-palette";
import {
  closePalette,
  openPalette,
  usePaletteOpen,
  usePaletteShortcut,
} from "@/lib/command-palette-store";
import { since } from "@/lib/relative-dates";
import { goToAddress } from "@/lib/url-state";

/**
 * Where one goes, without leaving the keyboard.
 *
 * It navigates and nothing else: every line is a place, and opening one from
 * here leaves exactly the trace that clicking it would have. Writing from a
 * palette is another feature, and one that would have to say out loud what the
 * screens say by refusing.
 *
 * It sits in the frame rather than on a screen, since it is reached from every
 * one of them; the reference list and the team are only asked for once it has
 * been opened.
 */
export function CommandPalette() {
  usePaletteShortcut();
  const open = usePaletteOpen();
  const router = useRouter();
  // Read at each draw rather than frozen at mount: the palette lives in the
  // frame, which outlasts a working day, and « hier » would go on being said.
  const now = new Date();

  // Archived projects included: the palette is the only place one is reached
  // without first going to a screen and undoing a filter.
  const { missions } = useProjects(true, open);
  const { teammates } = useTeammates(false, open);

  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const list = useRef<HTMLDivElement>(null);

  const all = useMemo(
    () => destinations({ missions, teammates }),
    [missions, teammates],
  );
  const sections = useMemo(() => grouped(matching(all, query)), [all, query]);
  // The sections read one after the other give back the ranked order: that is
  // the line the selection travels along, and what it must match on screen.
  const found = useMemo(() => sections.flatMap((section) => section.items), [sections]);
  const current = Math.min(active, Math.max(found.length - 1, 0));

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

  useEffect(() => {
    list.current
      ?.querySelector('[data-active="true"]')
      ?.scrollIntoView({ block: "nearest" });
  }, [current]);

  function go(destination: Destination | undefined) {
    if (!destination) return;
    closePalette();

    const here = `${window.location.pathname}${window.location.search}`;
    if (destination.href === here) return;

    // The screen one is already standing on does not mount again, and Next's
    // router would move the address without a word to what reads it.
    if (destination.href.split("?")[0] === window.location.pathname) {
      goToAddress(destination.href);
    } else {
      router.push(destination.href);
    }
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (found.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((index) => (index + 1) % found.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => (index - 1 + found.length) % found.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      go(found[current]);
    }
  }

  return (
    <Dialog
      open={open}
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
            aria-activedescendant={found[current]?.key}
            aria-label="Rechercher un projet, une personne ou un écran"
            placeholder="Rechercher un projet, une personne ou un écran…"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setActive(0);
            }}
            onKeyDown={onKeyDown}
            className="min-w-0 flex-1 bg-transparent text-sm focus:outline-none"
          />
        </div>

        {found.length === 0 ? (
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
            {sections.map((section) => (
              <div key={section.group} role="group" aria-label={section.label}>
                <p
                  aria-hidden
                  className="px-2 pt-2 pb-1 text-xs font-medium tracking-wide text-slate-400"
                >
                  {section.label}
                </p>
                <ul>
                  {section.items.map((destination) => {
                    const selected = destination === found[current];
                    // When it moved comes before what it belongs to: this
                    // section is read for the first, and the second only tells
                    // two close names apart.
                    const said = [
                      destination.at && since(destination.at, now),
                      destination.hint,
                    ]
                      .filter(Boolean)
                      .join(" · ");
                    return (
                      <li
                        key={destination.key}
                        id={destination.key}
                        role="option"
                        aria-selected={selected}
                        data-active={selected}
                        title={destination.label}
                        onClick={() => go(destination)}
                        onMouseMove={() => setActive(found.indexOf(destination))}
                        className={[
                          "flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-2 text-sm",
                          selected ? "bg-slate-100" : "",
                        ].join(" ")}
                      >
                        <span className="flex size-4 shrink-0 items-center justify-center">
                          {destination.Icon ? (
                            <destination.Icon
                              className="size-4 text-slate-400"
                              aria-hidden
                            />
                          ) : (
                            <span
                              aria-hidden
                              title={
                                destination.status
                                  ? phaseLabel(destination.status)
                                  : undefined
                              }
                              className={`size-2.5 rounded-full ${
                                destination.status
                                  ? phaseDot(destination.status)
                                  : "bg-slate-300"
                              }`}
                            />
                          )}
                        </span>

                        <span className="min-w-0 flex-1 truncate">
                          {destination.label}
                        </span>

                        {/* Capped, and cut before the name is: a package's
                            parent takes a whole line of its own, and what one
                            typed was the name. */}
                        {said && (
                          <span className="min-w-0 max-w-[40%] truncate text-xs text-slate-400">
                            {said}
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
