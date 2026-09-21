"use client";

import { useCallback } from "react";

import type { AuditLogPageResponse } from "@/lib/api/generated/model";
import { listProjectAuditLog } from "@/lib/api/generated/projects/projects";
import { PAGE_SIZE, usePagedAudit } from "@/lib/use-paged-audit";

export { PAGE_SIZE };

/** A mission's log, read page by page. */
export function useProjectAudit(projectId: number) {
  const read = useCallback(
    async (offset: number) => {
      const response = await listProjectAuditLog(projectId, {
        limit: PAGE_SIZE,
        offset,
      });
      return response.data as AuditLogPageResponse;
    },
    [projectId],
  );

  return usePagedAudit(`project:${projectId}`, read);
}
