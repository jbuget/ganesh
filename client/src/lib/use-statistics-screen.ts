"use client";

import { useState } from "react";

import type { PeriodRange, StatisticsResponse } from "@/lib/api/generated/model";
import { useStatistics } from "@/lib/api/queries";

/**
 * Beyond this share of entries caught up late, the coverage rate is no longer
 * a measure of the work: it measures the calendar.
 */
export const LATE_SHARE_ALERT = 0.2;

/** The window the screen opens on: a month of hindsight, without being a year. */
export const DEFAULT_RANGE: PeriodRange = "last_30_days";

/** Figures worth going to look at, rather than plain readings. */
export interface StatisticsAlerts {
  lateCatchUp: boolean;
  idleTeammates: boolean;
  /** Projects nobody can declare on until a trade is added. */
  withoutActivity: boolean;
  /** Projects whose next bug would reach nobody. */
  withoutTechLead: boolean;
  /** Followed projects nobody has said a word about for a fortnight. */
  silentFollowed: boolean;
}

/**
 * What deserves the eye, once the figures are in.
 *
 * A period that expects nobody cannot be behind: crying wolf every weekend
 * would teach the team to ignore the colour altogether.
 */
function alertsOf(statistics: StatisticsResponse | undefined): StatisticsAlerts {
  if (!statistics) {
    return {
      lateCatchUp: false,
      idleTeammates: false,
      withoutActivity: false,
      withoutTechLead: false,
      silentFollowed: false,
    };
  }

  const expectsSomething = statistics.period.working_days > 0;
  const late = statistics.freshness.late_share;

  return {
    lateCatchUp: late !== null && late !== undefined && late > LATE_SHARE_ALERT,
    idleTeammates: expectsSomething && statistics.adoption.idle.length > 0,
    withoutActivity: statistics.registry.without_activity > 0,
    withoutTechLead: statistics.stewardship.without_tech_lead > 0,
    silentFollowed: statistics.thread.silent > 0,
  };
}

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
    alerts: alertsOf(query.statistics),
  };
}
