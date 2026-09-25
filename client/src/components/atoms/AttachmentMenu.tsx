"use client";

import { Download, Maximize2, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface AttachmentMenuProps {
  /** Named in the label a screen reader hears: a grid holds a dozen of these. */
  filename: string;
  /** Shows the file at full size, in front of everything else. */
  onOpen: () => void;
  /** Asks to call it something else. What answers is a dialog. */
  /** Left out where a file may be read and not renamed. */
  onRename?: () => void;
  /**
   * Where the file is saved from.
   *
   * A plain address rather than a callback: saving a file is what a browser
   * does with a link, and going through `window.location` would leave the
   * page if the server ever answered `inline`.
   */
  downloadHref: string;
  /** Asks for it to go. What answers is a dialog. */
  /** Left out where a file may be read and not withdrawn. */
  onRemove?: () => void;
  /**
   * How the trigger is drawn, when the surface it sits on has its own look.
   *
   * Replaces the default pill rather than adding to it: two roundings on the
   * same button show one inside the other on hover, which reads as a glitch.
   */
  className?: string;
}

/**
 * What one does to a file, folded behind an icon.
 *
 * Same shape as `MissionMenu`: the card shows the file, the menu acts on it,
 * and what loses something sits last, where the hand does not land by
 * accident.
 */
const TRIGGER =
  "rounded p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700";

export function AttachmentMenu({
  filename,
  onOpen,
  onRename,
  downloadHref,
  onRemove,
  className = TRIGGER,
}: AttachmentMenuProps) {
  const [isOpen, setOpen] = useState(false);

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={`Actions sur « ${filename} »`}
        className={`cursor-pointer ${className}`}
      >
        <MoreHorizontal className="size-4" aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="end" className="w-52 p-1">
        <ul>
          <li>
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                onOpen();
              }}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
            >
              <Maximize2 className="size-4 shrink-0 text-slate-400" aria-hidden />
              Ouvrir
            </button>
          </li>

          {onRename && (
            <li>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  onRename();
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
              >
                <Pencil className="size-4 shrink-0 text-slate-400" aria-hidden />
                Renommer
              </button>
            </li>
          )}

          <li>
            <a
              href={downloadHref}
              download={filename}
              onClick={() => setOpen(false)}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
            >
              <Download className="size-4 shrink-0 text-slate-400" aria-hidden />
              Télécharger
            </a>
          </li>

          {onRemove && (
            <li>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  onRemove();
                }}
                className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm text-red-600 transition-colors hover:bg-red-50"
              >
                <Trash2 className="size-4 shrink-0" aria-hidden />
                Supprimer
              </button>
            </li>
          )}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
