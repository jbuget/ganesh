"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { MoodLevel } from "@/lib/api/generated/model";
import {
  clearMood,
  getGetMyMoodsQueryKey,
  setMood,
} from "@/lib/api/generated/moods/moods";
import { useMyMoods } from "@/lib/api/queries";
import { todayIso } from "@/lib/dates";

/**
 * What one may still answer for, and the answering itself.
 *
 * Only the mood query is replayed after a write, where the other screens
 * invalidate everything: nothing else on the home screen depends on a mood,
 * and refetching four months of grid to colour one face in would make the
 * cheapest gesture of the screen the most expensive.
 */
export function useMood() {
  const queryClient = useQueryClient();
  const { days, isLoading } = useMyMoods();
  // Which day is travelling, rather than a plain flag: two days are offered,
  // and one answer must not grey out the other.
  const [savingDay, setSavingDay] = useState<string | null>(null);

  return {
    isLoading,
    days,
    today: todayIso(),
    savingDay,

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
        await queryClient.invalidateQueries({ queryKey: getGetMyMoodsQueryKey() });
      } finally {
        setSavingDay(null);
      }
    },
  };
}
