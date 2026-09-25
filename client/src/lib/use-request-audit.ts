"use client";

import { useCallback } from "react";

import type { AuditLogPageResponse } from "@/lib/api/generated/model";
import { listRequestAuditLog } from "@/lib/api/generated/requests/requests";
import { PAGE_SIZE, usePagedAudit } from "@/lib/use-paged-audit";

/** A need's log, read page by page, as a mission's is. */
export function useRequestAudit(requestId: number) {
  const read = useCallback(
    async (offset: number) => {
      const response = await listRequestAuditLog(requestId, {
        limit: PAGE_SIZE,
        offset,
      });
      return response.data as AuditLogPageResponse;
    },
    [requestId],
  );

  return usePagedAudit(`request:${requestId}`, read);
}
