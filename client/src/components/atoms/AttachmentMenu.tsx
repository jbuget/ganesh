"use client";

import { Download, Maximize2, MoreHorizontal, Trash2 } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface AttachmentMenuProps {
  /** Named in the label a screen reader hears: a grid holds a dozen of these. */
  filename: string;
  /** Shows the file at full size, in front of everything else. */
  onOpen: () => void;
  /** Saves it, under the name it was dropped with. */
  onDownload: () => void;
  /** Asks for it to go. What answers is a dialog. */
  onRemove: () => void;
}

/**
 * What one does to a file, folded behind an icon.
 *
 * Same shape as `MissionMenu`: the card shows the file, the menu acts on it,
 * and what loses something sits last, where the hand does not land by
 * accident.
 */
export function AttachmentMenu({
  filename,
  onOpen,
  onDownload,
  onRemove,
}: AttachmentMenuProps) {
  const [isOpen, setOpen] = useState(false);

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={`Actions sur « ${filename} »`}
        className="cursor-pointer rounded p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
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

          <li>
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                onDownload();
              }}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
            >
              <Download className="size-4 shrink-0 text-slate-400" aria-hidden />
              Télécharger
            </button>
          </li>

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
        </ul>
      </PopoverContent>
    </Popover>
  );
}
