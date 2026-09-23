"use client";

import { useCallback } from "react";

import type { AuditLogPageResponse } from "@/lib/api/generated/model";
import { listUserAuditLog } from "@/lib/api/generated/users/users";
import { PAGE_SIZE, usePagedAudit } from "@/lib/use-paged-audit";

/** A teammate's log, read page by page. */
export function useUserAudit(userId: number) {
  const read = useCallback(
    async (offset: number) => {
      const response = await listUserAuditLog(userId, {
        limit: PAGE_SIZE,
        offset,
      });
      return response.data as AuditLogPageResponse;
    },
    [userId],
  );

  return usePagedAudit(`user:${userId}`, read);
}
