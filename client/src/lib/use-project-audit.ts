"use client";

import { useCallback, useEffect, useState } from "react";

import type { AuditLogPageResponse } from "@/lib/api/generated/model";
import { listProjectAuditLog } from "@/lib/api/generated/projects/projects";

/**
 * How many lines one page carries.
 *
 * A mission worked on for a year by a dozen people has thousands of lines: the
 * whole log is served, but a screenful at a time.
 */
export const PAGE_SIZE = 50;

/** What has been read, and of which mission it is the log. */
interface ReadSoFar extends AuditLogPageResponse {
  projectId: number;
}

/**
 * A mission's log, read page by page.
 *
 * Pages stack rather than replace one another: one scrolls back through the
 * mission's life without losing what has already been read.
 *
 * What was read carries the mission it belongs to, so that swapping missions
 * shows « Chargement… » rather than the previous log for a frame — and without
 * an effect having to wipe the state, which would cost a render.
 */
export function useProjectAudit(projectId: number) {
  const [read, setRead] = useState<ReadSoFar | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    listProjectAuditLog(projectId, { limit: PAGE_SIZE, offset: 0 }).then((response) => {
      if (!alive) return;
      const page = response.data as AuditLogPageResponse;
      setRead({ projectId, entries: page.entries, total: page.total });
    });
    return () => {
      alive = false;
    };
  }, [projectId]);

  const current = read?.projectId === projectId ? read : null;
  const entries = current?.entries ?? null;

  const loadMore = useCallback(async () => {
    if (current === null || busy) return;
    setBusy(true);
    try {
      const response = await listProjectAuditLog(projectId, {
        limit: PAGE_SIZE,
        offset: current.entries.length,
      });
      const page = response.data as AuditLogPageResponse;
      setRead({
        projectId,
        entries: [...current.entries, ...page.entries],
        // The count is read back with every page: a gesture made elsewhere
        // while the log was open would otherwise never show in the tally.
        total: page.total,
      });
    } finally {
      setBusy(false);
    }
  }, [busy, current, projectId]);

  return {
    entries,
    total: current?.total ?? 0,
    busy,
    hasMore: current !== null && current.entries.length < current.total,
    loadMore,
  };
}
