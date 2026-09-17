"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { BoardMemberResponse, ProjectRole } from "@/lib/api/generated/model";
import { assignMember, unassignMember } from "@/lib/api/generated/projects/projects";
import { useTeammates } from "@/lib/api/queries";

interface IntervenantsPickerProps {
  projectId: number;
  intervenants: BoardMemberResponse[];
  onChange: () => void | Promise<void>;
  /** A quel titre ces personnes sont rattachees a la mission. */
  role?: ProjectRole;
  /** Invite affichee quand personne n'est encore rattache. */
  invite?: string;
}

/** Au-dela, les pastilles se chevauchent trop pour rester lisibles. */
const VISIBLES = 4;

/**
 * Qui intervient sur une mission, en lecture et en modification.
 *
 * La liste se remanie deux fois par semaine : on l'ouvre d'un clic sur les
 * pastilles, et chaque nom bascule au clic suivant, sans validation ni
 * fermeture. Enchainer trois personnes ne demande donc que trois clics.
 */
export function IntervenantsPicker({
  projectId,
  intervenants,
  onChange,
  role = "intervenant",
  invite = "Intervenants",
}: IntervenantsPickerProps) {
  const { teammates } = useTeammates();
  const [ouvert, setOuvert] = useState(false);
  const affectes = new Set(intervenants.map((membre) => membre.id));

  async function basculer(memberId: number) {
    if (affectes.has(memberId)) {
      await unassignMember(projectId, memberId, { role });
    } else {
      await assignMember(projectId, memberId, { role });
    }
    await onChange();
  }

  const visibles = intervenants.slice(0, VISIBLES);
  const restants = intervenants.slice(VISIBLES);

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        aria-label={`Modifier les ${invite.toLowerCase()}`}
        className="flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 -mx-1 transition-colors hover:bg-slate-100"
      >
        {intervenants.length === 0 ? (
          <span className="flex items-center gap-1 text-xs text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            {invite}
          </span>
        ) : (
          <span className="flex items-center -space-x-1.5">
            {visibles.map((membre) => (
              <span
                key={membre.id}
                title={membre.display_name}
                className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-200 text-[10px] font-medium text-slate-700"
              >
                {membre.initiales}
              </span>
            ))}
            {restants.length > 0 && (
              <span className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-100 text-[10px] font-medium text-slate-500">
                +{restants.length}
              </span>
            )}
          </span>
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-56 p-1">
        <ul>
          {teammates.map((membre) => {
            const present = affectes.has(membre.id);
            return (
              <li key={membre.id}>
                <button
                  type="button"
                  aria-pressed={present}
                  onClick={() => void basculer(membre.id)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
                    {membre.initiales}
                  </span>
                  <span className="min-w-0 flex-1 truncate">{membre.display_name}</span>
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
