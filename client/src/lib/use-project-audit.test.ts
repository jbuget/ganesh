import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";

import { PAGE_SIZE, useProjectAudit } from "./use-project-audit";
import type { AuditLogEntryResponse } from "@/lib/api/generated/model";

const api = vi.hoisted(() => ({ listProjectAuditLog: vi.fn() }));

vi.mock("@/lib/api/generated/projects/projects", () => api);

function line(id: number): AuditLogEntryResponse {
  return {
    id,
    at: "2026-09-17T10:00:00",
    action: "project.update",
    actor: null,
    target_user: null,
    day: null,
    field: "label",
    old_value: null,
    new_value: null,
  };
}

/** A log of `total` lines, served page by page as the server would. */
function aLogOf(total: number) {
  api.listProjectAuditLog.mockImplementation(
    (_id: number, params: { limit: number; offset: number }) => {
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

async function log() {
  const { result } = renderHook(() => useProjectAudit(7));
  await waitFor(() => expect(result.current.entries).not.toBeNull());
  return result;
}

describe("useProjectAudit", () => {
  it("opens on the most recent page", async () => {
    aLogOf(120);
    const result = await log();

    expect(api.listProjectAuditLog).toHaveBeenCalledWith(7, {
      limit: PAGE_SIZE,
      offset: 0,
    });
    expect(result.current.entries).toHaveLength(PAGE_SIZE);
    expect(result.current.total).toBe(120);
    expect(result.current.hasMore).toBe(true);
  });

  it("adds the next page to what is already read", async () => {
    aLogOf(120);
    const result = await log();

    await act(async () => {
      await result.current.loadMore();
    });

    expect(api.listProjectAuditLog).toHaveBeenLastCalledWith(7, {
      limit: PAGE_SIZE,
      offset: PAGE_SIZE,
    });
    expect(result.current.entries).toHaveLength(2 * PAGE_SIZE);
    // Each line stays itself: a page appended twice would be read as a gesture
    // done twice.
    expect(new Set(result.current.entries?.map((one) => one.id)).size).toBe(
      2 * PAGE_SIZE,
    );
  });

  it("stops asking once the whole log has been read", async () => {
    aLogOf(PAGE_SIZE + 3);
    const result = await log();

    await act(async () => {
      await result.current.loadMore();
    });

    expect(result.current.entries).toHaveLength(PAGE_SIZE + 3);
    expect(result.current.hasMore).toBe(false);
  });

  it("has nothing more to offer on a mission nothing ever happened to", async () => {
    const result = await log();

    expect(result.current.entries).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.hasMore).toBe(false);
  });
});
