"use client";

import { PageHeader } from "@/components/atoms/PageHeader";
import { AuditLogFilters } from "@/components/molecules/AuditLogFilters";
import { AuditLogList } from "@/components/organisms/AuditLogList";
import { PageLayout } from "@/components/organisms/PageLayout";
import { hasAnyFilter } from "@/lib/audit-filters";
import { useAuditLog } from "@/lib/use-audit-log";

/**
 * The register, read across.
 *
 * A mission's « Journal » tab answers « what happened to this project », and a
 * month's history « what happened to this month ». Both are opened by somebody
 * who already knows where to look. This answers « what happened », which is
 * the question one puts when one does not — and the only screen where a
 * deletion can be found at all: the line survives its mission, but with no
 * mission left to open, no other screen can reach it.
 *
 * Nothing is sorted out and nothing is reserved. The register is what makes a
 * team that may enter a colleague's month trustworthy, and a register only
 * some may read would be a weaker promise than the one already made.
 */
export function AuditLogPage() {
  const { log, filters, change, clear } = useAuditLog();

  return (
    <PageLayout
      header={
        <>
          <PageHeader
            title="Journal"
            subtitle="Tout ce qui a été fait, du plus récent au plus ancien."
          />
          {/* With the header, outside the scrolling area: the question put to
              the register must stay readable and editable fifty lines down. */}
          <AuditLogFilters filters={filters} onChange={change} onClear={clear} />
        </>
      }
    >
      <AuditLogList
        log={log}
        reading={{ read: "all" }}
        emptiness={
          hasAnyFilter(filters)
            ? "Aucun geste ne répond à ces critères."
            : "Rien n'a encore été enregistré."
        }
      />
    </PageLayout>
  );
}
