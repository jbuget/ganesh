"use client";

import { Maximize2, X } from "lucide-react";
import Link from "next/link";

import { EditableTitle } from "@/components/atoms/EditableTitle";
import { ParentMissionLink } from "@/components/atoms/ParentMissionLink";
import { SidePanel } from "@/components/atoms/SidePanel";
import { ProjectTabs } from "@/components/organisms/ProjectTabs";
import { useProjectDetail } from "@/lib/use-project-detail";

interface ProjectPanelProps {
  projectId: number;
  /** What to open on: the sheet by default, the thread when that is what was aimed at. */
  tab?: string | null;
  onClose: () => void;
  /** Tells the board: a phase changed here moves a card there. */
  onMissionChanged: () => void | Promise<void>;
  /**
   * Swaps the panel for another mission — the project a work package belongs
   * to. The screen behind stays where it was.
   */
  onOpenMission: (projectId: number) => void;
}

/**
 * The mission opened beside the board.
 *
 * The kanban stays visible and usable behind: one looks at a mission without
 * losing sight of the column it comes from, nor of where one meant to drop it
 * next.
 */
export function ProjectPanel({
  projectId,
  tab,
  onClose,
  onMissionChanged,
  onOpenMission,
}: ProjectPanelProps) {
  const sheet = useProjectDetail(projectId, onMissionChanged);
  const detail = sheet.detail;

  return (
    <SidePanel label={detail ? detail.project.label : "Mission"} onClose={onClose}>
      <header className="border-b border-slate-200 px-5 py-4">
        {/* Above the title, therefore read before it: which whole this
              mission is a part of comes before its own name. */}
        {detail?.parent && (
          <ParentMissionLink parent={detail.parent} onOpen={onOpenMission} />
        )}

        <div className="flex items-center gap-2">
          <EditableTitle
            label={detail?.project.label ?? "Chargement…"}
            hint="Renommer la mission"
            onRename={detail ? sheet.rename : undefined}
          />

          <Link
            href={`/projects/${projectId}`}
            aria-label="Ouvrir en pleine page"
            className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <Maximize2 className="size-4" aria-hidden />
          </Link>
          <button
            type="button"
            aria-label="Fermer"
            onClick={onClose}
            className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="size-4" aria-hidden />
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-5 py-4">
        {sheet.notFound && (
          <p className="text-sm text-slate-500">Cette mission n&apos;existe pas.</p>
        )}
        {detail && (
          <ProjectTabs
            detail={detail}
            initialTab={tab}
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
            // The panel stays open after archiving, even though the mission
            // leaves the list behind: closing it on an unlucky click would
            // leave no way back, the row having gone from the reference
            // list. The banner and « Desarchiver » keep the return
            // within reach.
            archive={sheet.archive}
            // Deleting, unlike archiving, leaves nothing to come back to:
            // the panel closes, and the screen behind drops the row.
            deleteMission={async () => {
              await sheet.remove();
              onClose();
            }}
            unarchive={sheet.unarchive}
          />
        )}
      </div>
    </SidePanel>
  );
}
