"use client";

import { Check, UserPlus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { PlanMemberResponse } from "@/lib/api/generated/model";

interface PlanAssigneesPickerProps {
  /** Named in the labels, so the control says what it acts on. */
  label: string;
  /** Everyone the work could be placed on. */
  team: PlanMemberResponse[];
  assignees: PlanMemberResponse[];
  onChange: (userIds: number[]) => void;
}

/** Past this, the avatars overlap too much to stay readable. */
const VISIBLE = 3;

/**
 * Who a scenario supposes is on a mission.
 *
 * A sibling of `ContributorsPicker` rather than a reuse of it, and on purpose:
 * that one writes the assignment to the database on each click, which is
 * exactly what a projection must not do. This one is controlled and writes
 * nothing — the screen holds the hypothesis, the server is only asked what it
 * would cost. It has no search field either: the team is short, and it comes
 * with the plan rather than from a call of its own.
 */
export function PlanAssigneesPicker({
  label,
  team,
  assignees,
  onChange,
}: PlanAssigneesPickerProps) {
  const [isOpen, setOpen] = useState(false);
  const chosen = new Set(assignees.map((member) => member.id));

  function toggle(memberId: number) {
    const next = new Set(chosen);
    if (!next.delete(memberId)) next.add(memberId);
    // The order of the team is what counts: the same people always produce the
    // same request, whatever the order of the clicks.
    onChange(team.filter((member) => next.has(member.id)).map((member) => member.id));
  }

  const visible = assignees.slice(0, VISIBLE);
  const remaining = assignees.length - visible.length;

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={`Changer les intervenants de ${label}`}
        title={`Changer les intervenants de « ${label} »`}
        className="-mx-1 flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 transition-colors hover:bg-slate-100"
      >
        {assignees.length === 0 ? (
          <span className="flex items-center gap-1 text-sm text-slate-400">
            <UserPlus className="size-3.5" aria-hidden />
            Affecter
          </span>
        ) : (
          <span className="flex items-center -space-x-1.5">
            {visible.map((member) => (
              <span
                key={member.id}
                title={member.display_name}
                className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-200 text-[10px] font-medium text-slate-700"
              >
                {member.initials}
              </span>
            ))}
            {remaining > 0 && (
              <span className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-100 text-[10px] font-medium text-slate-500">
                +{remaining}
              </span>
            )}
          </span>
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-56 p-1">
        <ul className="max-h-64 overflow-y-auto overscroll-contain">
          {team.map((member) => {
            const present = chosen.has(member.id);
            return (
              <li key={member.id}>
                <button
                  type="button"
                  aria-pressed={present}
                  onClick={() => toggle(member.id)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
                    {member.initials}
                  </span>
                  <span className="min-w-0 flex-1 truncate">{member.display_name}</span>
                  {present && (
                    <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
