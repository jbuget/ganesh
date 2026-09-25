"use client";

import { AuditLogList } from "@/components/organisms/AuditLogList";
import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import { useRequestAudit } from "@/lib/use-request-audit";

interface RequestAuditSectionProps {
  requestId: number;
}

/**
 * Everything that ever happened to the need, at the foot of its sheet.
 *
 * The gestures were traced from the first day and nothing read them: a
 * register nobody can open is not one. It closes the panel rather than
 * opening it — one comes to read what is asked, and only then how it got
 * here.
 *
 * The need is not named on any line: the panel is the need.
 */
export function RequestAuditSection({ requestId }: RequestAuditSectionProps) {
  const log = useRequestAudit(requestId);

  return (
    <section className="mt-6">
      <SheetSectionTitle>Journal</SheetSectionTitle>
      <div className="mt-2">
        <AuditLogList
          log={log}
          reading={{ read: "request" }}
          emptiness="Rien n'a encore été enregistré sur cette demande."
        />
      </div>
    </section>
  );
}
