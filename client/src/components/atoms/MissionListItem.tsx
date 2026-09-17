"use client";

import { ChevronRight } from "lucide-react";

interface MissionListItemProps {
  label: string;
  /** Un lot se decale sous son projet, pour que la hierarchie se lise. */
  estLot?: boolean;
  onOpen: () => void;
}

/**
 * Une mission dans le referentiel : son nom, et rien d'autre.
 *
 * La ligne ne porte aucune action. Tout ce qui se modifie sur une mission se
 * fait dans son panneau, d'un seul endroit : une liste qui edite en place
 * multiplie les chemins vers la meme donnee, et les fait diverger.
 */
export function MissionListItem({
  label,
  estLot = false,
  onOpen,
}: MissionListItemProps) {
  return (
    <li>
      <button
        type="button"
        onClick={onOpen}
        className={[
          "group flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-left transition-colors hover:bg-slate-100",
          estLot ? "pl-9 text-sm text-slate-600" : "text-sm font-medium text-slate-800",
        ].join(" ")}
      >
        {estLot && (
          <span aria-hidden className="-ml-4 text-slate-300">
            └
          </span>
        )}
        <span className="min-w-0 flex-1 truncate">{label}</span>
        <ChevronRight
          aria-hidden
          className="size-4 shrink-0 text-slate-300 opacity-0 transition-opacity group-hover:opacity-100"
        />
      </button>
    </li>
  );
}
