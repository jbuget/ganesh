"use client";

import { Search, X } from "lucide-react";

import { FilterSelect } from "@/components/atoms/FilterSelect";
import { Input } from "@/components/ui/input";
import type {
  ProjectCategory,
  ProjectKind,
  ProjectPriority,
  ProjectStatus,
} from "@/lib/api/generated/model";
import { useTeammates } from "@/lib/api/queries";
import { CATEGORIES, PHASES, PRIORITES } from "@/lib/board";
import {
  ETATS_DE_MISSION,
  TYPES_DE_MISSION,
  type BoardFilters as Criteres,
  type EtatMission,
} from "@/lib/board-filters";

interface BoardFiltersProps {
  filtres: Criteres;
  actif: boolean;
  onChange: (changement: Partial<Criteres>) => void;
  onEffacer: () => void;
  /** Cartes affichees, et cartes que porte le tableau entier. */
  visibles: number;
  total: number;
}

/**
 * La barre de filtres du tableau.
 *
 * Un critere vide ne retranche rien : la barre part donc du tableau entier, et
 * chaque choix le reduit. Le decompte a droite dit toujours ce qu'on voit sur
 * ce que l'on pourrait voir, pour qu'un ecran presque vide s'explique de
 * lui-meme.
 */
export function BoardFilters({
  filtres,
  actif,
  onChange,
  onEffacer,
  visibles,
  total,
}: BoardFiltersProps) {
  const { teammates } = useTeammates();

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <div className="relative">
        <Search
          className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-slate-400"
          aria-hidden
        />
        <Input
          type="search"
          value={filtres.nom}
          onChange={(event) => onChange({ nom: event.target.value })}
          placeholder="Rechercher une mission"
          aria-label="Rechercher une mission"
          className="h-9 w-64 pl-8"
        />
      </div>

      <FilterSelect
        libelle="Phase"
        options={PHASES.map(({ statut, libelle, pastille }) => ({
          valeur: statut,
          libelle,
          vignette: (
            <span
              className={`size-2.5 shrink-0 rounded-full ${pastille}`}
              aria-hidden
            />
          ),
        }))}
        valeurs={filtres.phases}
        onChange={(valeurs) => onChange({ phases: valeurs as ProjectStatus[] })}
      />

      <FilterSelect
        libelle="Catégorie"
        options={CATEGORIES.map(({ valeur, libelle }) => ({ valeur, libelle }))}
        valeurs={filtres.categories}
        onChange={(valeurs) => onChange({ categories: valeurs as ProjectCategory[] })}
      />

      <FilterSelect
        libelle="Priorité"
        options={PRIORITES.map(({ valeur, libelle, pastille }) => ({
          valeur,
          libelle,
          vignette: (
            <span
              className={`size-2.5 shrink-0 rounded-full ${pastille}`}
              aria-hidden
            />
          ),
        }))}
        valeurs={filtres.priorites}
        onChange={(valeurs) => onChange({ priorites: valeurs as ProjectPriority[] })}
      />

      <FilterSelect
        libelle="Intervenant"
        options={teammates.map((membre) => ({
          valeur: String(membre.id),
          libelle: membre.display_name,
          vignette: (
            <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
              {membre.initiales}
            </span>
          ),
        }))}
        valeurs={filtres.intervenants.map(String)}
        onChange={(valeurs) => onChange({ intervenants: valeurs.map(Number) })}
      />

      <FilterSelect
        libelle="Type"
        options={TYPES_DE_MISSION.map(({ valeur, libelle }) => ({ valeur, libelle }))}
        valeurs={filtres.types}
        onChange={(valeurs) => onChange({ types: valeurs as ProjectKind[] })}
      />

      <FilterSelect
        libelle="État"
        options={ETATS_DE_MISSION.map(({ valeur, libelle }) => ({ valeur, libelle }))}
        valeurs={filtres.etats}
        onChange={(valeurs) => onChange({ etats: valeurs as EtatMission[] })}
      />

      {actif && (
        <>
          <button
            type="button"
            onClick={onEffacer}
            className="flex cursor-pointer items-center gap-1 rounded-md px-2 py-1.5 text-sm text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            <X className="size-3.5" aria-hidden />
            Effacer
          </button>

          <p className="ml-auto text-sm tabular-nums text-slate-500">
            {visibles} mission{visibles > 1 ? "s" : ""} sur {total}
          </p>
        </>
      )}
    </div>
  );
}
