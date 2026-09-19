"use client";

import { useState } from "react";

import type { PeriodRange } from "@/lib/api/generated/model";
import { useStatistics } from "@/lib/api/queries";

/**
 * Beyond this share of entries caught up late, the coverage rate is no longer
 * a measure of the work: it measures the calendar.
 */
export const LATE_SHARE_ALERT = 0.2;

/** The window the screen opens on: a month of hindsight, without being a year. */
export const DEFAULT_RANGE: PeriodRange = "last_30_days";

/**
 * State and data of the statistics screen.
 *
 * The window lives here rather than in the URL: the dashboard is read, not
 * linked to, and a range carried in the address would age badly — « the last
 * 30 days » does not mean the same thing a month later.
 */
export function useStatisticsScreen() {
  const [range, setRange] = useState<PeriodRange>(DEFAULT_RANGE);
  const query = useStatistics(range);

  return {
    range,
    setRange,
    statistics: query.statistics,
    isLoading: query.isLoading,
  };
}
