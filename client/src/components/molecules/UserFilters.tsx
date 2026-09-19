"use client";

import { Search, X } from "lucide-react";

import { FilterSelect } from "@/components/atoms/FilterSelect";
import { Input } from "@/components/ui/input";
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
  /** Teammates shown, and teammates the screen carries in all. */
  visible: number;
  total: number;
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
}: UserFiltersProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {/* An announced search group: a screen reader must be able to jump to the
          criteria, and know what they govern. */}
      <div role="search" aria-label="Filtrer les collaborateurs" className="contents">
        <div className="relative">
          <Search
            className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-slate-400"
            aria-hidden
          />
          <Input
            type="search"
            value={filters.name}
            onChange={(event) => onChange({ name: event.target.value })}
            placeholder="Rechercher un collaborateur"
            aria-label="Rechercher un collaborateur"
            className="h-9 w-64 pl-8"
          />
        </div>

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

        {hasFilter && (
          <button
            type="button"
            onClick={onClear}
            className="flex cursor-pointer items-center gap-1 rounded-md px-2 py-1.5 text-sm text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            <X className="size-3.5" aria-hidden />
            Effacer
          </button>
        )}
      </div>

      {hasFilter && (
        /*
          The count is spoken aloud: a filter that leaves nothing cannot be seen
          when one is not looking at the screen, and `status` announces it
          without interrupting typing.
        */
        <p role="status" className="ml-auto text-sm tabular-nums text-slate-500">
          {visible} collaborateur{visible > 1 ? "s" : ""} sur {total}
        </p>
      )}
    </div>
  );
}
