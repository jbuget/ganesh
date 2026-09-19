"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GROUPINGS, type Grouping } from "@/lib/roadmap";

interface GroupingSelectProps {
  value: Grouping;
  onChange: (value: Grouping) => void;
}

/**
 * How the lines are gathered into bands.
 *
 * The real setting of the screen: the grouping decides who the roadmap is
 * being shown to. A steering committee reads axes, a phase review reads
 * phases.
 */
export function GroupingSelect({ value, onChange }: GroupingSelectProps) {
  return (
    <Select value={value} onValueChange={(next) => onChange(next as Grouping)}>
      <SelectTrigger
        aria-label="Regroupement des missions"
        className="w-48 cursor-pointer"
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {GROUPINGS.map((grouping) => (
          <SelectItem
            key={grouping.value}
            value={grouping.value}
            className="cursor-pointer"
          >
            {grouping.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
