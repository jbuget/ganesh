"use client";

import { MoodPicker } from "@/components/atoms/MoodPicker";
import type { MoodLevel, OpenDayResponse } from "@/lib/api/generated/model";
import { dayLabel, mood } from "@/lib/mood";

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
 * Two days at most are offered, today and the working day before: past that
 * the window is closed, and a morale reconstituted a week later measures the
 * memory one keeps of the week rather than the days it was made of.
 */
export function MoodCheckIn({
  days,
  today,
  onPick,
  savingDay = null,
}: MoodCheckInProps) {
  if (days.length === 0) return null;

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-4">
      <header className="mb-3">
        <h2 className="text-sm font-semibold text-slate-900">Mon moral</h2>
        <p className="text-xs text-slate-500">
          Toute l&apos;équipe lit le résultat, et personne ne répond à votre place.
        </p>
      </header>

      <ul className="space-y-1">
        {days.map((open) => {
          const answered = mood(open.level);

          return (
            <li key={open.day} className="flex items-center gap-3">
              <span className="w-36 shrink-0 text-sm text-slate-700 first-letter:uppercase">
                {dayLabel(open.day, today)}
              </span>
              <MoodPicker
                value={open.level ?? null}
                onPick={(level) => onPick(open.day, level)}
                disabled={savingDay === open.day}
              />
              <span className="text-sm text-slate-500">
                {answered ? answered.label : "Pas encore de réponse"}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
