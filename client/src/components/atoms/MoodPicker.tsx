"use client";

import type { MoodLevel } from "@/lib/api/generated/model";
import { MOODS } from "@/lib/mood";

interface MoodPickerProps {
  /** What was already answered for this day, or null when nothing was. */
  value: MoodLevel | null;
  onPick: (level: MoodLevel) => void;
  /** While the answer travels: a second click would post a second time. */
  disabled?: boolean;
}

/**
 * The five faces one answers a day with.
 *
 * The one picked is the only one in colour; the others stand by in grey and
 * take their shade under the cursor. A day already answered therefore reads
 * without being read, and the row still offers the four other answers — one
 * changes one's mind about a day, and the grid must not have to be emptied
 * first.
 *
 * Clicking the face already chosen takes the answer back, which is why it
 * reads « Retirer » on hover: five small faces are easily mis-clicked, and the
 * whole team reads the result under one's name. The way out is the way in.
 */
export function MoodPicker({ value, onPick, disabled = false }: MoodPickerProps) {
  return (
    <div role="radiogroup" aria-label="Moral de la journée" className="flex gap-0.5">
      {MOODS.map((level) => {
        const Icon = level.icon;
        const picked = level.value === value;

        return (
          <button
            key={level.value}
            type="button"
            role="radio"
            aria-checked={picked}
            aria-label={picked ? `${level.label} — retirer` : level.label}
            title={picked ? "Retirer" : level.label}
            disabled={disabled}
            onClick={() => onPick(level.value)}
            className={[
              "cursor-pointer rounded-md p-1 transition-colors",
              "disabled:cursor-not-allowed disabled:opacity-50",
              picked ? `bg-slate-100 ${level.colour}` : `text-slate-300 ${level.hover}`,
            ].join(" ")}
          >
            <Icon className="size-6" aria-hidden />
          </button>
        );
      })}
    </div>
  );
}
