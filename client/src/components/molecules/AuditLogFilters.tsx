"use client";

import { ClearFilters } from "@/components/atoms/ClearFilters";
import { FilterSelect } from "@/components/atoms/FilterSelect";
import type { AuditAction } from "@/lib/api/generated/model";
import { useTeammates } from "@/lib/api/queries";
import { ACTION_FAMILIES, type AuditFilters, hasAnyFilter } from "@/lib/audit-filters";

interface AuditLogFiltersProps {
  filters: AuditFilters;
  onChange: (over: Partial<AuditFilters>) => void;
  onClear: () => void;
}

/**
 * The questions one puts to the register.
 *
 * Read across, the register is mostly declared time: a screenful of it answers
 * nothing one came for. The criteria are what make it answerable — which
 * gesture, whose, and when — and they narrow on the server, so the tally under
 * them counts the whole answer rather than the page.
 *
 * The gestures are offered by family, in the product's own divisions: thirty
 * of them in one flat list is a list read to the third line and abandoned.
 */
export function AuditLogFilters({ filters, onChange, onClear }: AuditLogFiltersProps) {
  // Everyone, deactivated accounts included: they acted while they were here,
  // and their gestures are still in the register.
  const { teammates } = useTeammates(true);

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <div role="search" aria-label="Filtrer le journal" className="contents">
        <FilterSelect
          label="Geste"
          options={ACTION_FAMILIES.flatMap((family) =>
            family.actions.map((action) => ({
              value: action.value,
              label: action.label,
              group: family.label,
            })),
          )}
          values={filters.actions}
          onChange={(values) => onChange({ actions: values as AuditAction[] })}
        />

        <FilterSelect
          label="Auteur"
          options={teammates.map((person) => ({
            value: String(person.id),
            label: person.display_name,
          }))}
          values={filters.actorIds}
          // One person at a time: the register answers a single actor, and
          // ticking a second would quietly drop the first.
          onChange={(values) => onChange({ actorIds: values.slice(-1) })}
        />

        {/* Days rather than moments: what one remembers is « mardi », and the
            register turns that into the day the team lived, both ends kept. */}
        <label className="flex items-center gap-1.5 text-sm text-slate-600">
          Du
          <input
            type="date"
            value={filters.fromDay}
            max={filters.toDay || undefined}
            onChange={(event) => onChange({ fromDay: event.target.value })}
            className="cursor-pointer rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-700 transition-colors hover:border-slate-400"
          />
        </label>

        <label className="flex items-center gap-1.5 text-sm text-slate-600">
          au
          <input
            type="date"
            value={filters.toDay}
            min={filters.fromDay || undefined}
            onChange={(event) => onChange({ toDay: event.target.value })}
            className="cursor-pointer rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-700 transition-colors hover:border-slate-400"
          />
        </label>
      </div>

      {hasAnyFilter(filters) && <ClearFilters onClear={onClear} />}
    </div>
  );
}
