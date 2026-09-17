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
  type MissionFilters as Criteres,
  type EtatMission,
} from "@/lib/mission-filters";

interface MissionFiltersProps {
  filtres: Criteres;
  actif: boolean;
  onChange: (changement: Partial<Criteres>) => void;
  onEffacer: () => void;
  /** Missions affichees, et missions que l'ecran porte en tout. */
  visibles: number;
  total: number;
}

/**
 * La barre de filtres d'un ecran de missions.
 *
 * Un critere vide ne retranche rien : la barre part donc du tableau entier, et
 * chaque choix le reduit. Le decompte a droite dit toujours ce qu'on voit sur
 * ce que l'on pourrait voir, pour qu'un ecran presque vide s'explique de
 * lui-meme.
 */
export function MissionFilters({
  filtres,
  actif,
  onChange,
  onEffacer,
  visibles,
  total,
}: MissionFiltersProps) {
  const { teammates } = useTeammates();

  return (
    // Un groupe de recherche annonce : le lecteur d'ecran doit pouvoir sauter
    // aux criteres, et savoir ce qu'ils gouvernent.
    <div
      role="search"
      aria-label="Filtrer les missions"
      className="mb-4 flex flex-wrap items-center gap-2"
    >
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
        options={CATEGORIES.map(({ valeur, libelle, puce }) => ({
          valeur,
          libelle,
          vignette: (
            <span className={`size-2.5 shrink-0 rounded-[3px] ${puce}`} aria-hidden />
          ),
        }))}
        valeurs={filtres.categories}
        onChange={(valeurs) => onChange({ categories: valeurs as ProjectCategory[] })}
      />

      <FilterSelect
        libelle="Priorité"
        options={PRIORITES.map(({ valeur, libelle, icone: Icone, couleur, trait }) => ({
          valeur,
          libelle,
          vignette: (
            <Icone
              className={`size-4 shrink-0 ${couleur}`}
              strokeWidth={trait}
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

          {/*
            Le decompte se dit a voix haute : un filtre qui ne laisse rien ne
            se voit pas quand on ne regarde pas l'ecran, et `status` l'annonce
            sans interrompre la frappe.
          */}
          <p role="status" className="ml-auto text-sm tabular-nums text-slate-500">
            {visibles} mission{visibles > 1 ? "s" : ""} sur {total}
          </p>
        </>
      )}
    </div>
  );
}
