"use client";

import { Check, Plus, Search } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useComboboxFilter } from "@/components/ui/combobox";
import type { BoardMemberResponse, ProjectRole } from "@/lib/api/generated/model";
import { assignMember, unassignMember } from "@/lib/api/generated/projects/projects";
import { useTeammates } from "@/lib/api/queries";

interface ContributorsPickerProps {
  projectId: number;
  contributors: BoardMemberResponse[];
  onChange: () => void | Promise<void>;
  /** On what grounds these people are attached to the mission. */
  role?: ProjectRole;
  /** Prompt shown when nobody is attached yet. */
  invite?: string;
}

/** Past this, the avatars overlap too much to stay readable. */
const VISIBLES = 4;

/**
 * Who works on a mission, to read and to change.
 *
 * The list is reworked twice a week: it opens with a click on the avatars, and
 * each name toggles on the next click, with no confirmation and no closing.
 * Three people in a row therefore take three clicks.
 *
 * The search field takes focus on opening: across a whole team, typing three
 * letters beats scrolling the list.
 */
export function ContributorsPicker({
  projectId,
  contributors,
  onChange,
  role = "contributor",
  invite = "Intervenants",
}: ContributorsPickerProps) {
  const { teammates } = useTeammates();
  const [ouvert, setOuvert] = useState(false);
  const [search, setRecherche] = useState("");
  // The same filter as the search menus elsewhere in the application:
  // insensitive to case and to accents alike.
  const { contains } = useComboboxFilter();
  const affectes = new Set(contributors.map((member) => member.id));

  const proposes = teammates.filter((member) => contains(member.display_name, search));

  async function toggle(memberId: number) {
    if (affectes.has(memberId)) {
      await unassignMember(projectId, memberId, { role });
    } else {
      await assignMember(projectId, memberId, { role });
    }
    await onChange();
  }

  const visible = contributors.slice(0, VISIBLES);
  const remaining = contributors.slice(VISIBLES);

  return (
    <Popover
      open={ouvert}
      onOpenChange={(prochain) => {
        setOuvert(prochain);
        if (!prochain) setRecherche("");
      }}
    >
      <PopoverTrigger
        aria-label={`Modifier les ${invite.toLowerCase()}`}
        className="flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 -mx-1 transition-colors hover:bg-slate-100"
      >
        {contributors.length === 0 ? (
          <span className="flex items-center gap-1 text-sm text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            {invite}
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
            {remaining.length > 0 && (
              <span className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-100 text-[10px] font-medium text-slate-500">
                +{remaining.length}
              </span>
            )}
          </span>
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-56 gap-0 p-1">
        {/*
          Negative margins: the popover has padding of its own, otherwise the
          rule under the field would stop short of the edges.
        */}
        <div className="-mx-1 flex items-center gap-2 border-b border-border px-2.5">
          <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          <input
            type="text"
            autoFocus
            value={search}
            aria-label={`Rechercher parmi les ${invite.toLowerCase()}`}
            placeholder="Rechercher…"
            onChange={(event) => setRecherche(event.target.value)}
            className="h-8 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
        </div>

        {proposes.length === 0 ? (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            Aucun collaborateur ne correspond.
          </p>
        ) : (
          <ul className="max-h-64 overflow-y-auto overscroll-contain pt-1">
            {proposes.map((member) => {
              const present = affectes.has(member.id);
              return (
                <li key={member.id}>
                  <button
                    type="button"
                    aria-pressed={present}
                    onClick={() => void toggle(member.id)}
                    className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                  >
                    <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
                      {member.initials}
                    </span>
                    <span className="min-w-0 flex-1 truncate">
                      {member.display_name}
                    </span>
                    {present && (
                      <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </PopoverContent>
    </Popover>
  );
}
