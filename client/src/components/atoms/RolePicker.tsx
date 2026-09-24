"use client";

import { Check } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Role } from "@/lib/api/generated/model";
import { ROLES, roleLabel } from "@/lib/roles";

interface RolePickerProps {
  role: Role;
  /**
   * Whether this reader may move this account at all.
   *
   * Nobody changes their own rank, and nobody acts on somebody standing
   * above them: the page works it out, the picker only draws the answer.
   */
  modifiable: boolean;
  /**
   * The ranks the reader may hand out — never above their own.
   *
   * Passed rather than derived: an atom reads no account. What is left out
   * is not shown, so a manager never sees « Administrateur » in the list and
   * then meets a refusal on clicking it.
   */
  grantable: Role[];
  onChange: (role: Role) => void | Promise<void>;
}

/**
 * A teammate's role, changed from the list.
 *
 * Without management rights, the role still shows: knowing who can reopen a
 * validated month concerns the whole team, not only those who decide it.
 */
export function RolePicker({ role, modifiable, grantable, onChange }: RolePickerProps) {
  const [isOpen, setOpen] = useState(false);
  // The rank held is always in the list, whether or not it may be handed out:
  // a picker that could not show what it is set to would read as empty.
  const choices = ROLES.filter(
    (choice) => choice.value === role || grantable.includes(choice.value),
  );

  if (!modifiable || choices.length < 2) {
    return <span className="text-sm text-slate-600">{roleLabel(role)}</span>;
  }

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={`Changer le rôle, actuellement ${roleLabel(role)}`}
        className="-mx-1 flex cursor-pointer items-center rounded px-1 py-0.5 text-sm text-slate-700 transition-colors hover:bg-slate-100"
      >
        {roleLabel(role)}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-72 p-1">
        <ul>
          {choices.map((choice) => (
            <li key={choice.value}>
              <button
                type="button"
                aria-pressed={choice.value === role}
                onClick={() => {
                  setOpen(false);
                  if (choice.value !== role) void onChange(choice.value);
                }}
                className="flex w-full cursor-pointer items-start gap-2 rounded px-2 py-1.5 text-left transition-colors hover:bg-slate-100"
              >
                <span className="min-w-0 flex-1">
                  <span className="block text-sm">{choice.label}</span>
                  <span className="block text-xs text-slate-500">
                    {choice.description}
                  </span>
                </span>
                {choice.value === role && (
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
