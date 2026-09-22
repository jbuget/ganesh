"use client";

import { ClearFilters } from "@/components/atoms/ClearFilters";
import { FilterSelect } from "@/components/atoms/FilterSelect";
import { FilteredCount } from "@/components/atoms/FilteredCount";
import { SearchField } from "@/components/atoms/SearchField";
import type { Department, RequestState } from "@/lib/api/generated/model";
import { DEPARTMENTS } from "@/lib/departments";
import type { RequestFilters as Criteria } from "@/lib/request-filters";
import { REQUEST_STATES } from "@/lib/requests";

interface RequestFiltersProps {
  filters: Criteria;
  hasFilter: boolean;
  onChange: (change: Partial<Criteria>) => void;
  onClear: () => void;
  /** Needs shown, and needs the screen carries in all. */
  visible: number;
  total: number;
}

/**
 * The filter bar of the list of needs.
 *
 * Three criteria and no more: what state it is in, whom it concerns, and the
 * search that finds one by name. A need carries no phase, no axis and no
 * priority — those belong to the mission it may become.
 */
export function RequestFilters({
  filters,
  hasFilter,
  onChange,
  onClear,
  visible,
  total,
}: RequestFiltersProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <SearchField
        value={filters.search}
        label="Rechercher une demande"
        onChange={(search) => onChange({ search })}
      />

      <FilterSelect
        label="État"
        options={REQUEST_STATES.map((state) => ({
          value: state.value,
          label: state.label,
          thumbnail: <span className={`size-2.5 shrink-0 rounded-full ${state.dot}`} />,
        }))}
        values={filters.states}
        onChange={(states) => onChange({ states: states as RequestState[] })}
      />

      <FilterSelect
        label="Département"
        options={DEPARTMENTS.map((department) => ({
          value: department.value,
          label: department.label,
        }))}
        values={filters.departments}
        onChange={(departments) =>
          onChange({ departments: departments as Department[] })
        }
      />

      {hasFilter && <ClearFilters onClear={onClear} />}

      <div className="ml-auto">
        <FilteredCount visible={visible} total={total} one="demande" many="demandes" />
      </div>
    </div>
  );
}
