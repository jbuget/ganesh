"use client";

import { useState } from "react";

import { WeekPatternPicker } from "@/components/atoms/WeekPatternPicker";
import { Button } from "@/components/ui/button";
import type { WorkRhythmResponse } from "@/lib/api/generated/model";
import { formatSpelledDate } from "@/lib/dates";
import { type WeekPattern, firstOfMonth, formatRhythm, patternOf } from "@/lib/rhythm";

interface UserRhythmProps {
  /** Null while nothing was declared, which reads as full time. */
  rhythm: WorkRhythmResponse | null | undefined;
  /** True on one's own account alone: everybody declares their own. */
  editable: boolean;
  today: Date;
  onDeclare: (pattern: WeekPattern, effectiveFrom: string) => void | Promise<void>;
}

/**
 * How much of a week somebody works, and since when.
 *
 * Read by the whole team — staffing somebody rests on knowing they are off on
 * Wednesdays — and written by them alone. Why they work four days is never
 * asked for, and there is nowhere here to say it.
 *
 * The motif is held until it is sent: three clicks to say « Wednesday off »
 * would otherwise be three declarations, and three lines in the register.
 */
export function UserRhythm({ rhythm, editable, today, onDeclare }: UserRhythmProps) {
  const declared = patternOf(rhythm);
  const [draft, setDraft] = useState<WeekPattern | null>(null);
  const [effectiveFrom, setEffectiveFrom] = useState(firstOfMonth(today));

  const shown = draft ?? declared;
  const changed = draft !== null && !sameAs(draft, declared);

  return (
    <div className="space-y-2">
      <WeekPatternPicker
        pattern={shown}
        editable={editable}
        onChange={(pattern) => setDraft(pattern)}
      />

      <p className="text-sm text-slate-700">
        {formatRhythm(shown)}
        {rhythm && !changed && (
          <span className="ml-2 text-xs text-slate-400">
            depuis le {formatSpelledDate(rhythm.effective_from)}
          </span>
        )}
        {!rhythm && !changed && (
          <span className="ml-2 text-xs text-slate-400">rythme non déclaré</span>
        )}
      </p>

      {changed && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs text-slate-500" htmlFor="rhythm-effective-from">
            À partir du
          </label>
          {/* Free rather than pinned to today: one catches up on a change made
              in March, and the coverage of March is the reason to. */}
          <input
            id="rhythm-effective-from"
            type="date"
            value={effectiveFrom}
            onChange={(event) => setEffectiveFrom(event.target.value)}
            className="cursor-pointer rounded border border-slate-300 px-2 py-1 text-sm"
          />
          <Button
            type="button"
            size="sm"
            className="cursor-pointer"
            onClick={async () => {
              await onDeclare(draft, effectiveFrom);
              setDraft(null);
            }}
          >
            Enregistrer
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className="cursor-pointer"
            onClick={() => setDraft(null)}
          >
            Annuler
          </Button>
        </div>
      )}
    </div>
  );
}

function sameAs(one: WeekPattern, other: WeekPattern): boolean {
  return (Object.keys(one) as (keyof WeekPattern)[]).every(
    (day) => one[day] === other[day],
  );
}
