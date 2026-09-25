"use client";

import { MoodPicker } from "@/components/atoms/MoodPicker";
import type { MoodLevel, OpenDayResponse } from "@/lib/api/generated/model";
import { dayLabel, mood } from "@/lib/mood";
import { STRONG_RULE } from "@/lib/table-frame";

interface MoodCheckInProps {
  /** The days one may still answer for, the most recent first. */
  days: OpenDayResponse[];
  today: string;
  onPick: (day: string, level: MoodLevel) => void;
  /** The day whose answer is travelling, if any. */
  savingDay?: string | null;
}

/**
 * How the day went, answered from the home screen.
 *
 * The only block of this screen that writes, and deliberately so: a mood is a
 * one-second gesture, and a screen of its own to make it would cost more than
 * the answer is worth — nobody would cross it twice.
 *
 * Nothing is offered until one answers: the five faces stand by in grey, and a
 * day left alone stays a day nobody answered for. Pre-picking « neutre » would
 * have the screen answer in one's place, and a morale made of defaults
 * measures the default.
 *
 * Two days at most are offered, today and the working day before: past that
 * the window is closed, and a morale reconstituted a week later measures the
 * memory one keeps of the week rather than the days it was made of.
 *
 * The day sits on its own line above the faces: the block lives in the narrow
 * column, where a label and five faces side by side would not fit.
 *
 * Closed at the weight the whole application closes an object at, where every
 * other block of the column takes the faint line. It is the one thing on this
 * screen that asks something of the reader, and a question drawn like the
 * notices around it gets read like a notice.
 */
export function MoodCheckIn({
  days,
  today,
  onPick,
  savingDay = null,
}: MoodCheckInProps) {
  if (days.length === 0) return null;

  return (
    <section className={`rounded-xl border bg-white p-3 ${STRONG_RULE}`}>
      <header className="mb-2">
        <h2 className="text-sm font-medium text-slate-700">Mon moral</h2>
        <p className="text-xs text-slate-400">
          Toute l&apos;équipe lit le résultat, et personne ne répond à votre place.
        </p>
      </header>

      <ul className="space-y-2">
        {days.map((open) => {
          const answered = mood(open.level);

          return (
            <li key={open.day}>
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-xs text-slate-500 first-letter:uppercase">
                  {dayLabel(open.day, today)}
                </span>
                <span className="text-xs text-slate-400">
                  {answered ? answered.label : "Pas encore de réponse"}
                </span>
              </div>
              <MoodPicker
                value={open.level ?? null}
                onPick={(level) => onPick(open.day, level)}
                disabled={savingDay === open.day}
              />
            </li>
          );
        })}
      </ul>
    </section>
  );
}
