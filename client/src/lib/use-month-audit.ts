"use client";

import { useCallback } from "react";

import type { AuditLogPageResponse } from "@/lib/api/generated/model";
import { listMonthAuditLog } from "@/lib/api/generated/months/months";
import { PAGE_SIZE, usePagedAudit } from "@/lib/use-paged-audit";

/**
 * The life of one month, read page by page.
 *
 * Whose month it is has to be said: the same month belongs to everybody, and
 * the screen is already looking at one person's. Until the screen knows whose,
 * nothing is asked for — everybody's month is not what an unanswered question
 * means.
 */
export function useMonthAudit(month: string, userId: number | null) {
  const read = useCallback(
    async (offset: number) => {
      if (userId === null) return { entries: [], total: 0 };
      const response = await listMonthAuditLog(month, {
        user_id: userId,
        limit: PAGE_SIZE,
        offset,
      });
      return response.data as AuditLogPageResponse;
    },
    [month, userId],
  );

  return usePagedAudit(`month:${month}:${userId ?? ""}`, read);
}
