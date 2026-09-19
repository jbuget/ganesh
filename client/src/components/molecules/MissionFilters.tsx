"use client";

import { ClearFilters } from "@/components/atoms/ClearFilters";
import { FilterSelect } from "@/components/atoms/FilterSelect";
import { FilteredCount } from "@/components/atoms/FilteredCount";
import { SearchField } from "@/components/atoms/SearchField";
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
  type MissionFilters as Criteria,
  type MissionState,
} from "@/lib/mission-filters";

interface MissionFiltersProps {
  filters: Criteria;
  hasFilter: boolean;
  onChange: (change: Partial<Criteria>) => void;
  onClear: () => void;
  /** Missions shown, and missions the screen carries in all. */
  visible: number;
  total: number;
  /**
   * What the screen hangs at the far end of the bar, next to the count.
   *
   * The bar knows how to filter and nothing else: the reference list puts the
   * choice of columns there, the kanban has none to offer, and neither has to
   * be told about the other.
   */
  trailing?: React.ReactNode;
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
  onClear,
  visible,
  total,
  trailing,
}: MissionFiltersProps) {
  const { teammates } = useTeammates();

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {/* An announced search group: a screen reader must be able to jump to the
          criteria, and know what they govern. It lays out nothing of its own —
          the criteria sit on the bar's own line, and what accompanies them is
          not part of the search. */}
      <div role="search" aria-label="Filtrer les projets" className="contents">
        <SearchField
          value={filters.name}
          onChange={(name) => onChange({ name })}
          label="Rechercher un projet"
        />

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
              <span
                className={`size-2.5 shrink-0 rounded-[3px] ${bullet}`}
                aria-hidden
              />
            ),
          }))}
          values={filters.categories}
          onChange={(values) => onChange({ categories: values as ProjectCategory[] })}
        />

        <FilterSelect
          label="Priorité"
          options={PRIORITIES.map(({ value, label, icon: Icon, colour }) => ({
            value,
            label,
            thumbnail: <Icon className={`size-4 shrink-0 ${colour}`} aria-hidden />,
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
          onChange={(values) => onChange({ states: values as MissionState[] })}
        />

        {hasFilter && <ClearFilters onClear={onClear} />}
      </div>

      {/* Pushed to the far end: what one reads about the list, and what one
          sets about how to read it, away from the criteria themselves. */}
      <div className="ml-auto flex items-center gap-2">
        {hasFilter && (
          <FilteredCount visible={visible} total={total} one="projet" many="projets" />
        )}
        {trailing}
      </div>
    </div>
  );
}
