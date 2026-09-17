"use client";

import { Archive, ArchiveRestore, MoreHorizontal } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface MissionMenuProps {
  /** Si la mission a deja quitte le referentiel. */
  archivee: boolean;
  /** Sort la mission du referentiel courant, sans la supprimer. */
  onArchiver: () => void | Promise<void>;
  /** La remet au referentiel. */
  onDesarchiver: () => void | Promise<void>;
}

/**
 * Ce qu'on fait a une mission entiere, replie derriere une icone.
 *
 * Les onglets editent le contenu de la mission ; ces actions-la portent sur la
 * mission elle-meme. Les tenir a l'ecart evite qu'on archive en visant un
 * onglet, et laisse la place aux suivantes sans redessiner l'en-tete.
 */
export function MissionMenu({ archivee, onArchiver, onDesarchiver }: MissionMenuProps) {
  const [ouvert, setOuvert] = useState(false);

  // Une seule entree, qui dit dans quel sens elle fait bouger la mission :
  // proposer les deux laisserait choisir l'etat ou l'on est deja.
  const Icone = archivee ? ArchiveRestore : Archive;

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
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
                setOuvert(false);
                void (archivee ? onDesarchiver() : onArchiver());
              }}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
            >
              <Icone className="size-4 shrink-0 text-slate-400" aria-hidden />
              {archivee ? "Désarchiver" : "Archiver"}
            </button>
          </li>
        </ul>
      </PopoverContent>
    </Popover>
  );
}
