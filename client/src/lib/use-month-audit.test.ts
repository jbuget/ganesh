import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";

import type { AuditLogEntryResponse } from "@/lib/api/generated/model";
import { PAGE_SIZE } from "@/lib/use-paged-audit";
import { useMonthAudit } from "./use-month-audit";

const api = vi.hoisted(() => ({ listMonthAuditLog: vi.fn() }));

vi.mock("@/lib/api/generated/months/months", () => api);

function line(id: number): AuditLogEntryResponse {
  return {
    id,
    at: "2026-09-17T10:00:00",
    action: "entry.set",
    actor: null,
    target_user: null,
    project: null,
    day: "2026-09-17",
    field: null,
    old_value: null,
    new_value: "1.0",
  };
}

function aLogOf(total: number) {
  api.listMonthAuditLog.mockImplementation(
    (_month: string, params: { limit: number; offset: number }) => {
      const all = Array.from({ length: total }, (_, rank) => line(rank + 1));
      return Promise.resolve({
        data: {
          total,
          entries: all.slice(params.offset, params.offset + params.limit),
        },
      });
    },
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  aLogOf(0);
});

describe("useMonthAudit", () => {
  it("opens on the most recent page of that person's month", async () => {
    aLogOf(3);
    const { result } = renderHook(() => useMonthAudit("2026-09-01", 7));

    await waitFor(() => expect(result.current.entries).not.toBeNull());

    expect(api.listMonthAuditLog).toHaveBeenCalledWith("2026-09-01", {
      user_id: 7,
      limit: PAGE_SIZE,
      offset: 0,
    });
    expect(result.current.total).toBe(3);
  });

  it("asks nothing while it does not know whose month to read", async () => {
    // The screen knows the month before it knows who is looking at it: asking
    // for everybody's month is not what an unanswered question means.
    const { result } = renderHook(() => useMonthAudit("2026-09-01", null));

    await waitFor(() => expect(result.current.entries).toEqual([]));

    expect(api.listMonthAuditLog).not.toHaveBeenCalled();
  });

  it("reads again when the month changes", async () => {
    aLogOf(1);
    const { rerender } = renderHook(({ month }) => useMonthAudit(month, 7), {
      initialProps: { month: "2026-09-01" },
    });
    await waitFor(() => expect(api.listMonthAuditLog).toHaveBeenCalledTimes(1));

    rerender({ month: "2026-08-01" });

    await waitFor(() =>
      expect(api.listMonthAuditLog).toHaveBeenLastCalledWith("2026-08-01", {
        user_id: 7,
        limit: PAGE_SIZE,
        offset: 0,
      }),
    );
  });
});
