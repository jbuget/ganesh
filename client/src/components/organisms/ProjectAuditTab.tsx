"use client";

import { AuditLogList } from "@/components/organisms/AuditLogList";
import { useProjectAudit } from "@/lib/use-project-audit";

interface ProjectAuditTabProps {
  projectId: number;
}

/**
 * Everything that ever happened to the mission.
 *
 * Nothing is sorted out: time declared sits beside a phase changed, because a
 * log that chose what deserves to be in it would no longer answer the question
 * one opens it with.
 *
 * The mission is not named on any line: it is the page, and its name on every
 * row would say nothing.
 */
export function ProjectAuditTab({ projectId }: ProjectAuditTabProps) {
  const log = useProjectAudit(projectId);

  return (
    <AuditLogList
      log={log}
      reading={{ read: "project" }}
      emptiness="Rien n'a encore été enregistré sur ce projet."
    />
  );
}
