"use client";

import { Check } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Role } from "@/lib/api/generated/model";
import { ROLES, libelleRole } from "@/lib/roles";

interface RolePickerProps {
  role: Role;
  /** Seul un manager promeut ou retrograde un collaborateur. */
  modifiable: boolean;
  onChange: (role: Role) => void | Promise<void>;
}

/**
 * Role d'un collaborateur, change depuis la liste.
 *
 * Sans droit de gestion, le role reste affiche : savoir qui peut rouvrir un
 * mois validé concerne toute l'équipe, pas seulement ceux qui le décident.
 */
export function RolePicker({ role, modifiable, onChange }: RolePickerProps) {
  const [ouvert, setOuvert] = useState(false);

  if (!modifiable) {
    return <span className="text-sm text-slate-600">{libelleRole(role)}</span>;
  }

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        aria-label={`Changer le rôle, actuellement ${libelleRole(role)}`}
        className="-mx-1 flex cursor-pointer items-center rounded px-1 py-0.5 text-sm text-slate-700 transition-colors hover:bg-slate-100"
      >
        {libelleRole(role)}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-72 p-1">
        <ul>
          {ROLES.map((choix) => (
            <li key={choix.valeur}>
              <button
                type="button"
                aria-pressed={choix.valeur === role}
                onClick={() => {
                  setOuvert(false);
                  if (choix.valeur !== role) void onChange(choix.valeur);
                }}
                className="flex w-full cursor-pointer items-start gap-2 rounded px-2 py-1.5 text-left transition-colors hover:bg-slate-100"
              >
                <span className="min-w-0 flex-1">
                  <span className="block text-sm">{choix.libelle}</span>
                  <span className="block text-xs text-slate-500">
                    {choix.description}
                  </span>
                </span>
                {choix.valeur === role && (
                  <Check className="mt-0.5 size-4 shrink-0 text-sky-600" aria-hidden />
                )}
              </button>
            </li>
          ))}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
