"use client";

import type { LucideIcon } from "lucide-react";

interface CardCounterProps {
  icone: LucideIcon;
  nombre: number;
  /** Ce que l'icone compte, au singulier puis au pluriel. */
  libelle: [string, string];
  /** Ce qu'annonce le lecteur d'ecran quand il n'y a rien a compter. */
  vide: string;
}

/**
 * Un decompte en pied de carte : une icone, et un nombre quand il y en a un.
 *
 * L'icone reste en place a zero, sans nombre a cote : la carte garde la meme
 * forme d'une mission a l'autre, et l'absence se lit alors aussi vite qu'un
 * total. C'est le parti pris de Monday, dont les cartes nous servent de
 * reference.
 */
export function CardCounter({ icone: Icone, nombre, libelle, vide }: CardCounterProps) {
  const [singulier, pluriel] = libelle;

  return (
    <span
      aria-label={nombre === 0 ? vide : `${nombre} ${nombre > 1 ? pluriel : singulier}`}
      className={`flex items-center gap-1 text-xs tabular-nums ${
        nombre === 0 ? "text-slate-300" : "text-slate-500"
      }`}
    >
      {nombre > 0 && nombre}
      <Icone className="size-3.5 shrink-0" aria-hidden />
    </span>
  );
}
