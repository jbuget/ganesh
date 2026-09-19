"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { MoodLevel } from "@/lib/api/generated/model";
import { getGetMyMoodsQueryKey, setMood } from "@/lib/api/generated/moods/moods";
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

    async post(day: string, level: MoodLevel) {
      setSavingDay(day);
      try {
        await setMood({ day, level });
        await queryClient.invalidateQueries({ queryKey: getGetMyMoodsQueryKey() });
      } finally {
        setSavingDay(null);
      }
    },
  };
}
