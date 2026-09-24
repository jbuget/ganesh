"use client";

import { ClearFilters } from "@/components/atoms/ClearFilters";
import { FilterSelect } from "@/components/atoms/FilterSelect";
import { FilteredCount } from "@/components/atoms/FilteredCount";
import { SearchField } from "@/components/atoms/SearchField";
import type { Role } from "@/lib/api/generated/model";
import { ROLES } from "@/lib/roles";
import {
  USER_STATES,
  type UserFilters as Criteria,
  type UserState,
} from "@/lib/user-filters";

interface UserFiltersProps {
  filters: Criteria;
  hasFilter: boolean;
  onChange: (change: Partial<Criteria>) => void;
  onClear: () => void;
  /** Teammates shown, and teammates one would see with no criterion. */
  visible: number;
  total: number;
  /** Guests the criteria are keeping out of sight, if any. */
  hidden: number;
  onShowGuests: () => void;
}

/**
 * The filter bar of the team list.
 *
 * It reads like the mission one, because it is the same gesture: an empty
 * criterion takes nothing away, every choice narrows the list, and the count on
 * the right always says what is seen against what could be seen, so that a
 * nearly empty screen explains itself.
 */
export function UserFilters({
  filters,
  hasFilter,
  onChange,
  onClear,
  visible,
  total,
  hidden,
  onShowGuests,
}: UserFiltersProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {/* An announced search group: a screen reader must be able to jump to the
          criteria, and know what they govern. */}
      <div role="search" aria-label="Filtrer les collaborateurs" className="contents">
        <SearchField
          value={filters.name}
          onChange={(name) => onChange({ name })}
          label="Rechercher un collaborateur"
        />

        <FilterSelect
          label="Rôle"
          options={ROLES.map(({ value, label }) => ({ value, label }))}
          values={filters.roles}
          onChange={(values) => onChange({ roles: values as Role[] })}
        />

        <FilterSelect
          label="Statut"
          options={USER_STATES.map(({ value, label }) => ({ value, label }))}
          values={filters.states}
          onChange={(values) => onChange({ states: values as UserState[] })}
        />

        {hasFilter && <ClearFilters onClear={onClear} />}
      </div>

      <div className="ml-auto flex items-center gap-4">
        {/* The list shows the team and hides everybody who only ever comes to
            ask for something. Said here rather than left to be discovered:
            three hundred accounts missing without a word is what makes
            somebody look for one they were never shown. */}
        {hidden > 0 && (
          <button
            type="button"
            onClick={onShowGuests}
            className="cursor-pointer text-sm text-slate-500 underline-offset-2 transition-colors hover:text-slate-900 hover:underline"
          >
            {hidden > 1 ? `Afficher les ${hidden} invités` : "Afficher l'invité"}
          </button>
        )}

        {hasFilter && (
          <FilteredCount
            visible={visible}
            total={total}
            one="collaborateur"
            many="collaborateurs"
          />
        )}
      </div>
    </div>
  );
}
