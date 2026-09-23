"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import type { MoodLevel } from "@/lib/api/generated/model";
import {
  dismissMoodReminder,
  useMoodReminderDismissedOn,
} from "@/lib/mood-reminder-store";
import { useMood } from "@/lib/use-mood";

/**
 * From when the day is over enough to be answered for.
 *
 * Read on the clock of the machine the reader sits at, which is the only one
 * that knows what time it is for them.
 */
export const REMINDER_FROM_HOUR = 16;

/**
 * How often the hour is looked at again.
 *
 * Looked at rather than read once: the frame outlasts a working day, and a tab
 * left open since the morning would otherwise never reach four o'clock.
 */
const TICK_MS = 60_000;

/**
 * How long the reader is left alone after landing somewhere.
 *
 * Somebody who has just opened a screen opened it to read it, and a panel
 * rising over that is an interruption whatever it asks. Long enough to have
 * found what one came for, short enough that the question still belongs to
 * the screen one is on.
 */
export const REMINDER_DELAY_MS = 4_000;

/**
 * The screens that already ask the question, and where it is not asked twice.
 *
 * « Moral » is the one that matters. Answering there would be answering under
 * the eyes of what the answer is about — the whole reason that screen reads
 * and never writes. The relance goes to the reader instead, which is what
 * lets the rule stand.
 *
 * The home screen already carries the check-in at the head of its right-hand
 * column: a panel posted over it would be noise.
 */
const ASKED_ELSEWHERE = ["/", "/mood"];

/**
 * The hour where the reader sits, or null until the browser has said.
 *
 * Null on the server and on the first client render: the server has no idea
 * what time it is in Paris, and a reminder drawn on a guess would have React
 * find two different pages on hydration.
 */
function useLocalHour(): number | null {
  const [hour, setHour] = useState<number | null>(null);

  useEffect(() => {
    const look = () => setHour(new Date().getHours());
    look();
    const tick = setInterval(look, TICK_MS);
    return () => clearInterval(tick);
  }, []);

  return hour;
}

/**
 * Whether the reader has been left alone long enough to be asked.
 *
 * The wait starts again at each screen, so whoever is still moving around is
 * never caught on arrival — but only until the question has been put once.
 * After that it stands: a relance that went back into hiding at every
 * navigation would rise again at the next one, and a panel that comes and goes
 * is read as a fault rather than as a question.
 */
function useSettledIn(pathname: string): boolean {
  const [waited, setWaited] = useState(false);
  const asked = useRef(false);

  useEffect(() => {
    if (asked.current) return;

    setWaited(false);
    const timer = setTimeout(() => {
      asked.current = true;
      setWaited(true);
    }, REMINDER_DELAY_MS);
    return () => clearTimeout(timer);
  }, [pathname]);

  return waited;
}

/**
 * Whether to ask for today's mood, and the answering itself.
 *
 * Today alone, never the working day before: this is a relance about the day
 * one is finishing, not a form to catch up on the week. The home screen keeps
 * the two open days, and stays where one answers deliberately.
 *
 * Nothing has to be said here about weekends or public holidays: `open_days`
 * decides in the domain what may still be answered for, so a Saturday carries
 * no today at all and the question cannot be asked.
 */
export function useMoodReminder() {
  const mood = useMood();
  const pathname = usePathname();
  const dismissedOn = useMoodReminderDismissedOn();
  const hour = useLocalHour();
  const settled = useSettledIn(pathname);

  const today = mood.today;
  const open = mood.days.find((day) => day.day === today);

  return {
    show:
      open != null &&
      open.level == null &&
      settled &&
      hour !== null &&
      hour >= REMINDER_FROM_HOUR &&
      !ASKED_ELSEWHERE.includes(pathname) &&
      dismissedOn !== today,

    /** While the answer travels: a second click would post a second time. */
    saving: mood.savingDay === today,

    post: (level: MoodLevel) => mood.post(today, level),

    /** Turned down until tomorrow, and believed. */
    dismiss: () => dismissMoodReminder(today),
  };
}
