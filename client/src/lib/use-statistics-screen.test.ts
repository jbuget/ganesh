import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DEFAULT_RANGE, useStatisticsScreen } from "./use-statistics-screen";
import type { StatisticsResponse } from "@/lib/api/generated/model";

const answer = vi.hoisted(() => ({
  statistics: undefined as StatisticsResponse | undefined,
  isLoading: false,
  asked: [] as string[],
}));

vi.mock("@/lib/api/queries", () => ({
  useStatistics: (range: string) => {
    answer.asked.push(range);
    return { statistics: answer.statistics, isLoading: answer.isLoading };
  },
}));

function statisticsWith(
  overrides: Partial<StatisticsResponse> = {},
): StatisticsResponse {
  return {
    period: {
      range: "last_30_days",
      start: "2026-08-19",
      end: "2026-09-17",
      working_days: 22,
    },
    coverage: {
      declared_days: 142,
      expected_days: 163,
      missing_days: 21,
      rate: 0.87,
      delta_in_points: 6,
    },
    freshness: {
      entries: 220,
      median_delay: 1.5,
      day_to_day_share: 0.68,
      late_share: 0.09,
    },
    month_validation: { validated: 9, due: 12, rate: 0.75 },
    adoption: {
      contributors: 11,
      expected_contributors: 12,
      rate: 0.91,
      idle: [{ id: 4, display_name: "L. Chen" }],
    },
    steering: {
      project_days: 120,
      off_project_days: 22,
      project_share: 0.85,
      by_status: [],
      by_category: [],
      top_missions: [],
    },
    registry: {
      active_missions: 30,
      missions_with_time: 18,
      missions_without_time: 12,
      usage_rate: 0.6,
      created: 2,
    },
    ...overrides,
  };
}

beforeEach(() => {
  answer.statistics = statisticsWith();
  answer.isLoading = false;
  answer.asked = [];
});

describe("useStatisticsScreen", () => {
  it("opens on a month of hindsight", () => {
    const { result } = renderHook(() => useStatisticsScreen());

    expect(result.current.range).toBe(DEFAULT_RANGE);
    expect(answer.asked).toContain("last_30_days");
  });

  it("asks again when the window changes", () => {
    const { result } = renderHook(() => useStatisticsScreen());

    act(() => result.current.setRange("last_7_days"));

    expect(result.current.range).toBe("last_7_days");
    expect(answer.asked).toContain("last_7_days");
  });

  it("flags a period mostly caught up after the fact", () => {
    answer.statistics = statisticsWith({
      freshness: {
        entries: 220,
        median_delay: 20,
        day_to_day_share: 0.1,
        late_share: 0.32,
      },
    });

    const { result } = renderHook(() => useStatisticsScreen());

    expect(result.current.alerts.lateCatchUp).toBe(true);
  });

  it("leaves a healthy freshness unflagged", () => {
    const { result } = renderHook(() => useStatisticsScreen());

    expect(result.current.alerts.lateCatchUp).toBe(false);
  });

  it("flags teammates who declared nothing", () => {
    const { result } = renderHook(() => useStatisticsScreen());

    expect(result.current.alerts.idleTeammates).toBe(true);
  });

  it("raises no alarm over a period nobody was expected in", () => {
    // A Saturday: « nobody declared anything » is the weekend, not a finding.
    answer.statistics = statisticsWith({
      period: {
        range: "today",
        start: "2026-09-19",
        end: "2026-09-19",
        working_days: 0,
      },
    });

    const { result } = renderHook(() => useStatisticsScreen());

    expect(result.current.alerts.idleTeammates).toBe(false);
  });

  it("raises no alarm while the figures are still on their way", () => {
    answer.statistics = undefined;
    answer.isLoading = true;

    const { result } = renderHook(() => useStatisticsScreen());

    expect(result.current.alerts).toEqual({
      lateCatchUp: false,
      idleTeammates: false,
    });
  });
});
