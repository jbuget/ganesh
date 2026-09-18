"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { EditableTitle } from "@/components/atoms/EditableTitle";
import { PageLayout } from "@/components/organisms/PageLayout";
import { ProjectTabs } from "@/components/organisms/ProjectTabs";
import { phaseLabel, phaseDot } from "@/lib/board";
import { formatDecimalDays } from "@/lib/dates";
import { useProjectDetail } from "@/lib/use-project-detail";

interface ProjectDetailPageProps {
  projectId: number;
}

/** The way back, in the same place in every state of the sheet. */
function RetourKanban() {
  return (
    <Link
      href="/kanban"
      className="mb-4 inline-flex cursor-pointer items-center gap-1.5 text-sm text-slate-500 transition-colors hover:text-slate-800"
    >
      <ArrowLeft className="size-4" aria-hidden />
      Kanban
    </Link>
  );
}

/**
 * The mission on a full page.
 *
 * The same content as the side panel, with room to breathe: to read a service
 * sheet or go through a log, space counts.
 */
export function ProjectDetailPage({ projectId }: ProjectDetailPageProps) {
  const fiche = useProjectDetail(projectId);
  const detail = fiche.detail;

  if (fiche.introuvable) {
    return (
      <PageLayout header={<RetourKanban />}>
        <p className="text-sm text-slate-500">Cette mission n&apos;existe pas.</p>
      </PageLayout>
    );
  }

  if (!detail) {
    return (
      <PageLayout header={<RetourKanban />}>
        <p className="text-sm text-slate-500">Chargement…</p>
      </PageLayout>
    );
  }

  const { project } = detail;

  return (
    <PageLayout
      header={
        <>
          <RetourKanban />

          <header className="mb-6">
            <EditableTitle
              label={project.label}
              invite="Renommer la mission"
              onRename={fiche.renommer}
              niveau={1}
            />
            <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
              {project.status && (
                <span className="flex items-center gap-1.5">
                  <span
                    aria-hidden
                    className={`size-2.5 rounded-full ${phaseDot(project.status)}`}
                  />
                  {phaseLabel(project.status)}
                </span>
              )}
              <span>
                {formatDecimalDays(detail.consumed_days)}
                {project.estimated_days ? `/${project.estimated_days}` : ""} jrs.
                {project.estimated_days ? " estimés" : " consommés"}
              </span>
            </p>
          </header>
        </>
      }
    >
      <div className="max-w-[900px]">
        <ProjectTabs
          detail={detail}
          onChange={fiche.reload}
          saveSheet={fiche.saveSheet}
          saveDescription={fiche.saveDescription}
          changePhase={fiche.changePhase}
          updateFields={fiche.updateFields}
          addLink={fiche.addLink}
          removeLink={fiche.removeLink}
          archive={fiche.archive}
          desarchiver={fiche.desarchiver}
        />
      </div>
    </PageLayout>
  );
}
