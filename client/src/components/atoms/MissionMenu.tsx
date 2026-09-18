"use client";

import { Archive, ArchiveRestore, MoreHorizontal } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface MissionMenuProps {
  /** Whether the mission has already left the reference list. */
  archived: boolean;
  /** Takes the mission out of the current reference list, without deleting it. */
  onArchive: () => void | Promise<void>;
  /** Puts it back into the reference list. */
  onUnarchive: () => void | Promise<void>;
}

/**
 * What one does to a whole mission, folded behind an icon.
 *
 * The tabs edit the mission's content; these actions act on the mission
 * itself. Keeping them apart avoids archiving while aiming at a tab, and
 * leaves room for the next ones without redrawing the header.
 */
export function MissionMenu({ archived, onArchive, onUnarchive }: MissionMenuProps) {
  const [isOpen, setOpen] = useState(false);

  // A single entry, saying which way it moves the mission: offering both would
  // let one pick the state one is already in.
  const Icon = archived ? ArchiveRestore : Archive;

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label="Actions sur la mission"
        className="cursor-pointer rounded p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
      >
        <MoreHorizontal className="size-4" aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="end" className="w-44 p-1">
        <ul>
          <li>
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                void (archived ? onUnarchive() : onArchive());
              }}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
            >
              <Icon className="size-4 shrink-0 text-slate-400" aria-hidden />
              {archived ? "Désarchiver" : "Archiver"}
            </button>
          </li>
        </ul>
      </PopoverContent>
    </Popover>
  );
}
