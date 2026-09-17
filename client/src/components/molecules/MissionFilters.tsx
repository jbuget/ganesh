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
import { CATEGORIES, PHASES, PRIORITIES } from "@/lib/board";
import {
  MISSION_STATES,
  MISSION_KINDS,
  type MissionFilters as Criteres,
  type EtatMission,
} from "@/lib/mission-filters";

interface MissionFiltersProps {
  filters: Criteres;
  hasFilter: boolean;
  onChange: (change: Partial<Criteres>) => void;
  onEffacer: () => void;
  /** Missions affichees, et missions que l'ecran porte en tout. */
  visible: number;
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
  filters,
  hasFilter,
  onChange,
  onEffacer,
  visible,
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
          value={filters.name}
          onChange={(event) => onChange({ name: event.target.value })}
          placeholder="Rechercher une mission"
          aria-label="Rechercher une mission"
          className="h-9 w-64 pl-8"
        />
      </div>

      <FilterSelect
        label="Phase"
        options={PHASES.map(({ status, label, dot }) => ({
          value: status,
          label,
          thumbnail: (
            <span className={`size-2.5 shrink-0 rounded-full ${dot}`} aria-hidden />
          ),
        }))}
        values={filters.phases}
        onChange={(values) => onChange({ phases: values as ProjectStatus[] })}
      />

      <FilterSelect
        label="Catégorie"
        options={CATEGORIES.map(({ value, label, bullet }) => ({
          value,
          label,
          thumbnail: (
            <span className={`size-2.5 shrink-0 rounded-[3px] ${bullet}`} aria-hidden />
          ),
        }))}
        values={filters.categories}
        onChange={(values) => onChange({ categories: values as ProjectCategory[] })}
      />

      <FilterSelect
        label="Priorité"
        options={PRIORITIES.map(({ value, label, icon: Icone, colour }) => ({
          value,
          label,
          thumbnail: <Icone className={`size-4 shrink-0 ${colour}`} aria-hidden />,
        }))}
        values={filters.priorities}
        onChange={(values) => onChange({ priorities: values as ProjectPriority[] })}
      />

      <FilterSelect
        label="Intervenant"
        options={teammates.map((member) => ({
          value: String(member.id),
          label: member.display_name,
          thumbnail: (
            <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
              {member.initials}
            </span>
          ),
        }))}
        values={filters.contributors.map(String)}
        onChange={(values) => onChange({ contributors: values.map(Number) })}
      />

      <FilterSelect
        label="Type"
        options={MISSION_KINDS.map(({ value, label }) => ({ value, label }))}
        values={filters.types}
        onChange={(values) => onChange({ types: values as ProjectKind[] })}
      />

      <FilterSelect
        label="État"
        options={MISSION_STATES.map(({ value, label }) => ({ value, label }))}
        values={filters.states}
        onChange={(values) => onChange({ states: values as EtatMission[] })}
      />

      {hasFilter && (
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
            {visible} mission{visible > 1 ? "s" : ""} sur {total}
          </p>
        </>
      )}
    </div>
  );
}
