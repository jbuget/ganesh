"use client";

import { useCallback, useEffect, useState } from "react";

import type { AuditLogPageResponse } from "@/lib/api/generated/model";

/**
 * How many lines one page carries.
 *
 * A mission worked on for a year by a dozen people has thousands of lines: the
 * whole log is served, but a screenful at a time.
 */
export const PAGE_SIZE = 50;

/** What has been read, and of what it is the log. */
interface ReadSoFar extends AuditLogPageResponse {
  subject: string;
}

/**
 * A log, read page by page.
 *
 * Pages stack rather than replace one another: one scrolls back through a
 * life without losing what has already been read.
 *
 * What was read carries the subject it belongs to — a mission, a month —, so
 * that swapping subjects shows « Chargement… » rather than the previous log
 * for a frame, and without an effect having to wipe the state, which would
 * cost a render.
 */
export function usePagedAudit(
  subject: string,
  /**
   * Reads one page, from that offset on. It must be held steady across
   * renders — `useCallback` over what the subject is made of — or the log
   * would be read again for ever.
   */
  read: (offset: number) => Promise<AuditLogPageResponse>,
) {
  const [state, setState] = useState<ReadSoFar | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    read(0).then((page) => {
      if (!alive) return;
      setState({ subject, entries: page.entries, total: page.total });
    });
    return () => {
      alive = false;
    };
  }, [read, subject]);

  const current = state?.subject === subject ? state : null;
  const entries = current?.entries ?? null;

  const loadMore = useCallback(async () => {
    if (current === null || busy) return;
    setBusy(true);
    try {
      const page = await read(current.entries.length);
      setState({
        subject,
        entries: [...current.entries, ...page.entries],
        // The count is read back with every page: a gesture made elsewhere
        // while the log was open would otherwise never show in the tally.
        total: page.total,
      });
    } finally {
      setBusy(false);
    }
  }, [busy, current, read, subject]);

  return {
    entries,
    total: current?.total ?? 0,
    busy,
    hasMore: current !== null && current.entries.length < current.total,
    loadMore,
  };
}
