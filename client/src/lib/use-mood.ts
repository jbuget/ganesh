"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { MoodLevel } from "@/lib/api/generated/model";
import {
  clearMood,
  getGetMyMoodsQueryKey,
  getGetTeamMoodsQueryKey,
  setMood,
} from "@/lib/api/generated/moods/moods";
import { useMyMoods } from "@/lib/api/queries";
import { todayIso } from "@/lib/dates";
import { useMayWrite } from "@/lib/use-may-write";

/**
 * What one may still answer for, and the answering itself.
 *
 * The two mood queries are replayed after a write, and only those. Refetching
 * four months of grid to colour one face in would make the cheapest gesture of
 * the screen the most expensive — but « what the home screen shows » is the
 * wrong boundary, and reading it that way is what left the team screen showing
 * a mood that had already changed. What a write touches is what must be
 * replayed, wherever it is read: an answer posted here lands in the team's
 * fortnight, which is another screen entirely.
 */
export function useMood() {
  const queryClient = useQueryClient();
  const { days, isLoading } = useMyMoods();
  // The moods are a mirror the team holds up to itself, and a guest is not
  // yet in it: the faces show what the week held and take no answer.
  const mayWrite = useMayWrite();
  // Which day is travelling, rather than a plain flag: two days are offered,
  // and one answer must not grey out the other.
  const [savingDay, setSavingDay] = useState<string | null>(null);

  return {
    isLoading,
    days,
    today: todayIso(),
    savingDay,
    mayAnswer: mayWrite,

    /**
     * Answers for a day, or takes the answer back.
     *
     * Picking the face already chosen removes it: a day one has answered and
     * then thought better of is a day one has not answered for, and the gesture
     * that undoes is the same as the one that did.
     */
    async post(day: string, level: MoodLevel) {
      const posted = days.find((open) => open.day === day)?.level;
      setSavingDay(day);
      try {
        if (posted === level) {
          await clearMood(day);
        } else {
          await setMood({ day, level });
        }
        // Both, always: the answer one has just given is read on the home
        // screen and on the team's fortnight, and the two go stale together.
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getGetMyMoodsQueryKey() }),
          queryClient.invalidateQueries({ queryKey: getGetTeamMoodsQueryKey() }),
        ]);
      } finally {
        setSavingDay(null);
      }
    },
  };
}
