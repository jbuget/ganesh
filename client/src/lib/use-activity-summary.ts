"use client";

import { useState } from "react";

import type { PeriodRange } from "@/lib/api/generated/model";
import { DEFAULT_ACTIVITY_RANGE } from "@/lib/activity";
import { useActivitySummary as useActivitySummaryQuery } from "@/lib/api/queries";

/** Which way the matrix is read. Missions first: that is the question asked. */
export type ActivityView = "project" | "person";

/**
 * State and data of the Synthèse d'activité.
 *
 * The window lives here rather than in the URL, as it does on Statistiques:
 * two neighbouring readings that carried their state differently would be
 * one more thing to know before using either.
 */
export function useActivityScreen() {
  const [range, setRange] = useState<PeriodRange>(DEFAULT_ACTIVITY_RANGE);
  const [view, setView] = useState<ActivityView>("project");
  const query = useActivitySummaryQuery(range);

  return {
    range,
    setRange,
    view,
    setView,
    summary: query.summary,
    isLoading: query.isLoading,
    /** Re-reads the window: what the panel changes shows here too. */
    async refresh(): Promise<void> {
      await query.refetch();
    },
  };
}
