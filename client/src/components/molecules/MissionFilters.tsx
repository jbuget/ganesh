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
  /** Missions shown, and missions the screen carries in all. */
  visible: number;
  total: number;
}

/**
 * The filter bar of a mission screen.
 *
 * An empty criterion takes nothing away: the bar therefore starts from the
 * whole board, and every choice narrows it. The count on the right always says
 * what is seen against what could be seen, so that a nearly empty screen
 * explains itself.
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
    // An announced search group: a screen reader must be able to jump to the
    // criteria, and know what they govern.
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
            The count is spoken aloud: a filter that leaves nothing cannot be
            seen when one is not looking at the screen, and `status` announces
            it without interrupting typing.
          */}
          <p role="status" className="ml-auto text-sm tabular-nums text-slate-500">
            {visible} mission{visible > 1 ? "s" : ""} sur {total}
          </p>
        </>
      )}
    </div>
  );
}
