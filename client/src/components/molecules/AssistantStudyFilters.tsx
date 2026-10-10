"use client";

import { Download } from "lucide-react";

import { ClearFilters } from "@/components/atoms/ClearFilters";
import { FilterSelect } from "@/components/atoms/FilterSelect";
import type { ExportFormat, Judgement, UserResponse } from "@/lib/api/generated/model";
import { JUDGEMENTS, type StudyFilters, hasStudyFilter } from "@/lib/assistant-study";

interface AssistantStudyFiltersProps {
  filters: StudyFilters;
  teammates: UserResponse[];
  onChange: (over: Partial<StudyFilters>) => void;
  onClear: () => void;
  exportUrl: (format: ExportFormat) => string;
}

const DATE_FIELD =
  "cursor-pointer rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-700 transition-colors hover:border-slate-400";

/**
 * The questions one puts to the exchanges kept, and the file they make.
 *
 * The export sits with the criteria rather than under the table: it saves
 * exactly what they keep, every page of it, and reads as their consequence.
 */
export function AssistantStudyFilters({
  filters,
  teammates,
  onChange,
  onClear,
  exportUrl,
}: AssistantStudyFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <div role="search" aria-label="Filtrer les échanges" className="contents">
        <FilterSelect
          label="Personne"
          search="Rechercher un collaborateur"
          options={teammates.map((person) => ({
            value: String(person.id),
            label: person.display_name,
          }))}
          values={filters.askerIds}
          // One person at a time: the API answers a single asker.
          onChange={(values) => onChange({ askerIds: values.slice(-1) })}
        />

        <FilterSelect
          label="Avis"
          options={JUDGEMENTS}
          values={filters.judgement === "" ? [] : [filters.judgement]}
          onChange={(values) =>
            onChange({ judgement: (values.at(-1) as Judgement | undefined) ?? "" })
          }
        />

        <label className="flex items-center gap-1.5 text-sm text-slate-600">
          Du
          <input
            type="date"
            value={filters.fromDay}
            max={filters.toDay || undefined}
            onChange={(event) => onChange({ fromDay: event.target.value })}
            className={DATE_FIELD}
          />
        </label>

        <label className="flex items-center gap-1.5 text-sm text-slate-600">
          au
          <input
            type="date"
            value={filters.toDay}
            min={filters.fromDay || undefined}
            onChange={(event) => onChange({ toDay: event.target.value })}
            className={DATE_FIELD}
          />
        </label>
      </div>

      {hasStudyFilter(filters) && <ClearFilters onClear={onClear} />}

      <div className="ml-auto flex items-center gap-3 text-sm">
        <span className="text-slate-500">Exporter</span>
        {(["csv", "json"] as const).map((format) => (
          <a
            key={format}
            href={exportUrl(format)}
            download
            className="flex cursor-pointer items-center gap-1 text-slate-700 underline-offset-2 hover:underline"
          >
            <Download aria-hidden className="size-3.5" />
            {format.toUpperCase()}
          </a>
        ))}
      </div>
    </div>
  );
}
