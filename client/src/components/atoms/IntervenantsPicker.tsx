"use client";

import { Check, Plus, Search } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useComboboxFilter } from "@/components/ui/combobox";
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
 *
 * Le champ de recherche prend le focus a l'ouverture : sur une equipe entiere,
 * taper trois lettres va plus vite que derouler la liste.
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
  const [recherche, setRecherche] = useState("");
  // Le meme filtre que les menus de recherche du reste de l'application :
  // insensible a la casse comme aux accents.
  const { contains } = useComboboxFilter();
  const affectes = new Set(intervenants.map((membre) => membre.id));

  const proposes = teammates.filter((membre) =>
    contains(membre.display_name, recherche),
  );

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
        {intervenants.length === 0 ? (
          <span className="flex items-center gap-1 text-sm text-slate-400">
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

      <PopoverContent align="start" className="w-56 gap-0 p-1">
        {/*
          Marges negatives : le popover a son propre padding, sans quoi le trait
          sous le champ s'arreterait avant les bords.
        */}
        <div className="-mx-1 flex items-center gap-2 border-b border-border px-2.5">
          <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          <input
            type="text"
            autoFocus
            value={recherche}
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
            {proposes.map((membre) => {
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
                    <span className="min-w-0 flex-1 truncate">
                      {membre.display_name}
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
