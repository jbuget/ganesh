"use client";

import type { ReminderCadence } from "@/lib/api/generated/model";
import { REMINDER_CHOICES } from "@/lib/reminders";

interface ReminderCadenceFieldProps {
  /** The cadence currently in force. */
  value: ReminderCadence;
  onChange: (cadence: ReminderCadence) => void;
  /** True while the choice is on its way to the API. */
  isSaving?: boolean;
}

/**
 * How often one is written to: three choices, one in force.
 *
 * Real radios rather than styled buttons — the group is reachable with the
 * keyboard, announced as a group, and arrow keys move through it, none of
 * which comes for free from a row of `<button>`s.
 *
 * Each choice says what it means under its name. « Chaque semaine » alone
 * leaves the reader to guess which day and whether an empty week still writes;
 * a line of detail answers both, and is what stops somebody from picking
 * « Jamais » out of caution.
 */
export function ReminderCadenceField({
  value,
  onChange,
  isSaving = false,
}: ReminderCadenceFieldProps) {
  return (
    <fieldset disabled={isSaving} className="min-w-0">
      <legend className="sr-only">Fréquence des rappels par e-mail</legend>

      <div className="flex flex-col gap-2">
        {REMINDER_CHOICES.map((choice) => {
          const isChosen = choice.value === value;
          return (
            <label
              key={choice.value}
              className={[
                "flex cursor-pointer items-start gap-3 rounded-md border px-3 py-2.5 transition-colors",
                isChosen
                  ? "border-slate-900 bg-slate-50"
                  : "border-slate-200 hover:bg-slate-50",
                isSaving ? "cursor-progress opacity-60" : "",
              ].join(" ")}
            >
              <input
                type="radio"
                name="reminder-cadence"
                value={choice.value}
                checked={isChosen}
                disabled={isSaving}
                onChange={() => onChange(choice.value)}
                className="mt-0.5 size-4 shrink-0 cursor-pointer accent-slate-900"
              />
              <span className="min-w-0">
                <span className="block text-sm font-medium">{choice.label}</span>
                <span className="block text-xs text-slate-500">{choice.detail}</span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
