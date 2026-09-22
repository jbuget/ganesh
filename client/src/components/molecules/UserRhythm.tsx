"use client";

import { Trash2 } from "lucide-react";
import { useState } from "react";

import { WeekPatternPicker } from "@/components/atoms/WeekPatternPicker";
import { Button } from "@/components/ui/button";
import type { WorkRhythmResponse } from "@/lib/api/generated/model";
import { formatSpelledDate } from "@/lib/dates";
import { type WeekPattern, firstOfMonth, formatRhythm, patternOf } from "@/lib/rhythm";

interface UserRhythmProps {
  /**
   * Every rhythm declared, latest first; one of them may be in force.
   *
   * The whole history rather than today's alone: one may only add to it, so
   * without the list a rhythm entered on the wrong date would hold its place
   * for good, and the panel would go on announcing a change nobody meant.
   */
  rhythms: WorkRhythmResponse[];
  /** True on one's own account alone: everybody declares their own. */
  editable: boolean;
  today: Date;
  onDeclare: (pattern: WeekPattern, effectiveFrom: string) => void | Promise<void>;
  onWithdraw: (effectiveFrom: string) => void | Promise<void>;
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
export function UserRhythm({
  rhythms,
  editable,
  today,
  onDeclare,
  onWithdraw,
}: UserRhythmProps) {
  const inForce = rhythms.find((one) => one.is_in_force) ?? null;
  const declared = patternOf(inForce);
  // The day the rhythm in force opened on, so that correcting it replaces it.
  // The first of the month would slip underneath and go on being covered: the
  // API would answer, and nothing on the screen would move.
  const opensOn = inForce?.effective_from ?? firstOfMonth(today);

  const [draft, setDraft] = useState<WeekPattern | null>(null);
  const [effectiveFrom, setEffectiveFrom] = useState(opensOn);
  const [failed, setFailed] = useState<string | null>(null);

  const shown = draft ?? declared;
  const changed = draft !== null && !sameAs(draft, declared);

  function giveUp() {
    setDraft(null);
    setFailed(null);
    // The date goes back with the motif: left behind, it would silently date
    // the next declaration, which is how a rhythm ends up opening a month one
    // never asked for.
    setEffectiveFrom(opensOn);
  }

  return (
    <div className="space-y-3">
      <WeekPatternPicker
        pattern={shown}
        editable={editable}
        onChange={(pattern) => {
          setFailed(null);
          setDraft(pattern);
        }}
      />

      <p className="text-sm text-slate-700">
        {formatRhythm(shown)}
        {!changed && (
          <span className="ml-2 text-xs text-slate-400">
            {inForce
              ? `depuis le ${formatSpelledDate(inForce.effective_from)}`
              : "rythme non déclaré"}
          </span>
        )}
      </p>

      {changed && (
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-xs text-slate-500" htmlFor="rhythm-effective-from">
              À partir du
            </label>
            {/* Free rather than pinned to today: one catches up on a change
                made in March, and the coverage of March is the reason to. */}
            <input
              id="rhythm-effective-from"
              type="date"
              value={effectiveFrom}
              onChange={(event) => {
                setFailed(null);
                setEffectiveFrom(event.target.value);
              }}
              className="cursor-pointer rounded border border-slate-300 px-2 py-1 text-sm"
            />
            <Button
              type="button"
              size="sm"
              className="cursor-pointer"
              onClick={async () => {
                try {
                  await onDeclare(draft, effectiveFrom);
                  setDraft(null);
                  setFailed(null);
                } catch {
                  // The motif stays on screen: nothing anybody entered is lost
                  // to a refusal they can still act on.
                  setFailed("Ce rythme n'a pas pu être enregistré.");
                }
              }}
            >
              Enregistrer
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="cursor-pointer"
              onClick={giveUp}
            >
              Annuler
            </Button>
          </div>

          {inForce && effectiveFrom < inForce.effective_from && (
            <p className="text-xs text-amber-700">
              Ce rythme ouvrira avant celui du{" "}
              {formatSpelledDate(inForce.effective_from)}, qui restera en vigueur.
            </p>
          )}
        </div>
      )}

      {/* The history, from which one withdraws — shown from the first rhythm
          on. Hidden below two, it would vanish on the withdrawal that takes it
          from two to one, which reads as having deleted the lot; and the last
          rhythm left would have no way out at all. */}
      {rhythms.length > 0 && (
        <ul className="space-y-1 border-t border-slate-200 pt-2">
          {rhythms.map((one) => (
            <li
              key={one.effective_from}
              className="flex items-center gap-2 text-xs text-slate-500"
            >
              <span className="text-slate-700">
                {formatRhythm(patternOf(one)).replace(" par semaine", " / sem.")}
              </span>
              <span>à partir du {formatSpelledDate(one.effective_from)}</span>
              {one.is_in_force && <span className="text-sky-700">en vigueur</span>}
              {editable && (
                <button
                  type="button"
                  aria-label={`Retirer le rythme du ${formatSpelledDate(one.effective_from)}`}
                  onClick={async () => {
                    try {
                      await onWithdraw(one.effective_from);
                      setFailed(null);
                    } catch {
                      setFailed("Ce rythme n'a pas pu être retiré.");
                    }
                  }}
                  className="ml-auto cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-red-700"
                >
                  <Trash2 className="size-3.5" aria-hidden />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {failed && (
        <p role="alert" className="text-xs text-red-700">
          {failed}
        </p>
      )}
    </div>
  );
}

function sameAs(one: WeekPattern, other: WeekPattern): boolean {
  return (Object.keys(one) as (keyof WeekPattern)[]).every(
    (day) => one[day] === other[day],
  );
}
