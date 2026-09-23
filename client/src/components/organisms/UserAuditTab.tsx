"use client";

import { AuditLogList } from "@/components/organisms/AuditLogList";
import { useUserAudit } from "@/lib/use-user-audit";

interface UserAuditTabProps {
  userId: number;
}

/**
 * Everything the register holds on a teammate.
 *
 * Both sides of their id: what they did, and what was done to them. Nothing is
 * sorted out — time declared sits beside a role changed, as it does everywhere
 * else the register is read.
 *
 * Every line names its mission, as the register read across does: the panel is
 * a person, and « a ajouté un fichier » with no mission beside it names a
 * gesture nobody can place. The person is named on every line too, and that is
 * not a repetition: half of these lines were written by somebody else.
 */
export function UserAuditTab({ userId }: UserAuditTabProps) {
  const log = useUserAudit(userId);

  return (
    <AuditLogList
      log={log}
      reading={{ read: "all" }}
      emptiness="Rien n'a encore été enregistré sur cette personne."
    />
  );
}
