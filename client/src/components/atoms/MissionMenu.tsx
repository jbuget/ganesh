"use client";

import {
  Archive,
  ArchiveRestore,
  CornerDownRight,
  CornerLeftUp,
  MoreHorizontal,
  Trash2,
} from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface MissionMenuProps {
  /** Whether the mission has already left the reference list. */
  archived: boolean;
  /**
   * Makes the mission a slice of another project.
   *
   * Left out where the question does not arise: off-project work is not a
   * slice of anything.
   */
  onAttach?: () => void;
  /**
   * Takes the work package back out as a project of its own. Left out on a
   * mission that belongs to no one.
   */
  onDetach?: () => void;
  /** The project the mission belongs to, named in the entry that leaves it. */
  parentLabel?: string | null;
  /** Takes the mission out of the current reference list, without deleting it. */
  onArchive: () => void | Promise<void>;
  /** Puts it back into the reference list. */
  onUnarchive: () => void | Promise<void>;
  /**
   * Asks for the mission to disappear.
   *
   * Always offered, even on a mission that carries time: what answers is a
   * dialog, which either confirms or explains the refusal. Greying the entry
   * out would leave the question unanswered.
   */
  onDelete: () => void | Promise<void>;
}

/**
 * What one does to a whole mission, folded behind an icon.
 *
 * The tabs edit the mission's content; these actions act on the mission
 * itself. Keeping them apart avoids archiving while aiming at a tab, and
 * leaves room for the next ones without redrawing the header.
 */
export function MissionMenu({
  archived,
  onAttach,
  onDetach,
  parentLabel,
  onArchive,
  onUnarchive,
  onDelete,
}: MissionMenuProps) {
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

      <PopoverContent align="end" className="w-60 p-1">
        <ul>
          {/* Where the mission sits in the reference list comes first: it is
              the one action that changes what the other screens read of it,
              and it is read before those that take it out. */}
          {onAttach && (
            <li>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  onAttach();
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <CornerDownRight
                  className="size-4 shrink-0 text-slate-400"
                  aria-hidden
                />
                Rattacher à un projet…
              </button>
            </li>
          )}

          {onDetach && (
            <li>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  void onDetach();
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <CornerLeftUp className="size-4 shrink-0 text-slate-400" aria-hidden />
                {/* The project is named rather than implied: on a sheet opened
                    from a list, one does not always have its parent in mind. */}
                <span className="min-w-0 truncate">Détacher de « {parentLabel} »</span>
              </button>
            </li>
          )}

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

          {/* Under archiving, and last: the one action that loses something
              sits where the hand does not land by accident. */}
          <li>
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                void onDelete();
              }}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm text-red-600 transition-colors hover:bg-red-50"
            >
              <Trash2 className="size-4 shrink-0" aria-hidden />
              Supprimer
            </button>
          </li>
        </ul>
      </PopoverContent>
    </Popover>
  );
}
