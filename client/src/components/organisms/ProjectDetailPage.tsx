"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { EditableTitle } from "@/components/atoms/EditableTitle";
import { ParentMissionLink } from "@/components/atoms/ParentMissionLink";
import { PageLayout } from "@/components/organisms/PageLayout";
import { ProjectTabs } from "@/components/organisms/ProjectTabs";
import { phaseLabel, phaseDot } from "@/lib/board";
import { formatDecimalDays } from "@/lib/dates";
import { useWayBack, type WayBack } from "@/lib/navigation-trail";
import { useProjectDetail } from "@/lib/use-project-detail";

interface ProjectDetailPageProps {
  projectId: number;
}

const WAY_BACK =
  "mb-4 inline-flex cursor-pointer items-center gap-1.5 text-sm text-slate-500 transition-colors hover:text-slate-800";

/**
 * The way back, in the same place in every state of the sheet.
 *
 * A link when it leads to an address — it is then worth opening beside the
 * sheet. A button when it walks a step back, which is a gesture and not a
 * destination: only the browser knows where it lands.
 */
function BackLink({ wayBack }: { wayBack: WayBack }) {
  const arrow = <ArrowLeft className="size-4" aria-hidden />;

  if (wayBack.href === undefined) {
    return (
      <button type="button" onClick={wayBack.back} className={WAY_BACK}>
        {arrow}
        {wayBack.label}
      </button>
    );
  }

  return (
    <Link href={wayBack.href} className={WAY_BACK}>
      {arrow}
      {wayBack.label}
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
  const router = useRouter();
  // With nothing behind — a link shared, a new tab — the reference list is
  // where a sheet is found again, archived missions included, which the board
  // does not show.
  const wayBack = useWayBack({ href: "/projects", label: "Projets" });
  const sheet = useProjectDetail(projectId);
  const detail = sheet.detail;

  if (sheet.notFound) {
    return (
      <PageLayout header={<BackLink wayBack={wayBack} />}>
        <p className="text-sm text-slate-500">Ce projet n&apos;existe pas.</p>
      </PageLayout>
    );
  }

  if (!detail) {
    return (
      <PageLayout header={<BackLink wayBack={wayBack} />}>
        <p className="text-sm text-slate-500">Chargement…</p>
      </PageLayout>
    );
  }

  const { project } = detail;

  return (
    <PageLayout
      header={
        <>
          <BackLink wayBack={wayBack} />

          <header className="mb-6">
            {/* Above the title, therefore read before it: which whole this
                mission is a part of comes before its own name. */}
            {detail.parent && <ParentMissionLink parent={detail.parent} />}

            <EditableTitle
              label={project.label}
              hint="Renommer le projet"
              onRename={sheet.rename}
              level={1}
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
          onChange={sheet.reload}
          saveSheet={sheet.saveSheet}
          saveDescription={sheet.saveDescription}
          changePhase={sheet.changePhase}
          updateFields={sheet.updateFields}
          saveRegistry={sheet.saveRegistry}
          addLink={sheet.addLink}
          removeLink={sheet.removeLink}
          addSubProject={sheet.addSubProject}
          attachTo={sheet.attachTo}
          detach={sheet.detach}
          archive={sheet.archive}
          // The page one is standing on no longer exists: the kanban is where
          // one came from, and where there is still something to read.
          deleteMission={async () => {
            await sheet.remove();
            router.push("/kanban");
          }}
          unarchive={sheet.unarchive}
        />
      </div>
    </PageLayout>
  );
}
