"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";

import { TableHead } from "@/components/ui/table";
import type { ColonneTri, TriMissions } from "@/lib/mission-sort";

interface SortableColumnHeaderProps {
  colonne: ColonneTri;
  libelle: string;
  tri: TriMissions;
  onBasculer: (colonne: ColonneTri) => void;
  /** Les colonnes de nombres s'alignent a droite, en-tete compris. */
  aDroite?: boolean;
}

/**
 * Un en-tete de colonne sur lequel on range le tableau.
 *
 * La double fleche ne parait qu'au survol de l'en-tete vise : neuf colonnes
 * qui reclameraient l'attention en meme temps ne diraient plus laquelle ordonne
 * la liste. Celle qui la range, elle, garde sa fleche affichee.
 */
export function SortableColumnHeader({
  colonne,
  libelle,
  tri,
  onBasculer,
  aDroite = false,
}: SortableColumnHeaderProps) {
  const actif = tri.colonne === colonne;
  const croissant = tri.sens === "asc";

  return (
    <TableHead
      aria-sort={actif ? (croissant ? "ascending" : "descending") : "none"}
      className={aDroite ? "text-right" : undefined}
    >
      <button
        type="button"
        onClick={() => onBasculer(colonne)}
        className={`group -mx-1 flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 transition-colors hover:bg-slate-200 ${
          aDroite ? "ml-auto" : ""
        }`}
      >
        {libelle}
        {actif ? (
          croissant ? (
            <ArrowUp className="size-3.5 shrink-0" aria-label="Ordre croissant" />
          ) : (
            <ArrowDown className="size-3.5 shrink-0" aria-label="Ordre décroissant" />
          )
        ) : (
          <ChevronsUpDown
            className="size-3.5 shrink-0 text-slate-400 opacity-0 transition-opacity group-hover:opacity-100"
            aria-hidden
          />
        )}
      </button>
    </TableHead>
  );
}
