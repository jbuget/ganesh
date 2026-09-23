"use client";

import { useCallback, useMemo, useState } from "react";

import type {
  AuditLogPageResponse,
  ListAuditLogParams,
} from "@/lib/api/generated/model";
import { listAuditLog } from "@/lib/api/generated/audit-logs/audit-logs";
import { type AuditFilters, NO_FILTER } from "@/lib/audit-filters";
import { PAGE_SIZE, usePagedAudit } from "@/lib/use-paged-audit";

/**
 * What the criteria become on the wire.
 *
 * An empty criterion is left out rather than sent empty: the API reads an
 * empty list of gestures as « none of them », which is right for a reader who
 * cleared every box and wrong for one who never opened it.
 */
export function asQuery(filters: AuditFilters): ListAuditLogParams {
  const query: ListAuditLogParams = { limit: PAGE_SIZE, offset: 0 };
  if (filters.actions.length > 0) query.action = filters.actions;
  // One person at a time on the wire: the register answers a single actor, and
  // the picker keeps to one so that what is asked is what is offered.
  if (filters.actorIds.length > 0) query.actor_id = Number(filters.actorIds[0]);
  if (filters.fromDay !== "") query.from_day = filters.fromDay;
  if (filters.toDay !== "") query.to_day = filters.toDay;
  return query;
}

/**
 * The whole register, narrowed and read page by page.
 *
 * The criteria are the subject the pages stack under: changing one starts the
 * reading over rather than appending an answer to another question.
 */
export function useAuditLog() {
  const [filters, setFilters] = useState<AuditFilters>(NO_FILTER);

  const query = useMemo(() => asQuery(filters), [filters]);
  const subject = useMemo(() => JSON.stringify(query), [query]);

  const read = useCallback(
    async (offset: number) => {
      const response = await listAuditLog({ ...query, offset });
      return response.data as AuditLogPageResponse;
    },
    [query],
  );

  const log = usePagedAudit(subject, read);

  const change = useCallback((over: Partial<AuditFilters>) => {
    setFilters((current) => ({ ...current, ...over }));
  }, []);

  const clear = useCallback(() => setFilters(NO_FILTER), []);

  return { log, filters, change, clear };
}
