"use client";

import { Maximize2, X } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

import { EditableTitle } from "@/components/atoms/EditableTitle";
import { ProjectTabs } from "@/components/organisms/ProjectTabs";
import { useProjectDetail } from "@/lib/use-project-detail";

interface ProjectPanelProps {
  projectId: number;
  /** Sur quoi s'ouvrir : la fiche par defaut, le fil si c'est lui qu'on visait. */
  onglet?: string | null;
  onClose: () => void;
  /** Tells the board: a phase changed here moves a card there. */
  onMissionChanged: () => void | Promise<void>;
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
  onglet,
  onClose,
  onMissionChanged,
}: ProjectPanelProps) {
  const fiche = useProjectDetail(projectId, onMissionChanged);
  const detail = fiche.detail;

  useEffect(() => {
    const fermerSurEchap = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", fermerSurEchap);
    return () => window.removeEventListener("keydown", fermerSurEchap);
  }, [onClose]);

  return (
    <>
      {/*
        The veil closes on click but does not hide: the board must stay
        readable, which is the whole point of a panel rather than a page.
      */}
      <div
        aria-hidden
        onClick={onClose}
        className="fixed inset-0 z-40 bg-slate-900/5"
      />

      <aside
        aria-label={detail ? detail.project.label : "Mission"}
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[40rem] flex-col border-l border-slate-300 bg-white shadow-xl"
      >
        <header className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
          <EditableTitle
            label={detail?.project.label ?? "Chargement…"}
            invite="Renommer la mission"
            onRename={detail ? fiche.renommer : undefined}
          />

          <Link
            href={`/projets/${projectId}`}
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
        </header>

        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-5 py-4">
          {fiche.introuvable && (
            <p className="text-sm text-slate-500">Cette mission n&apos;existe pas.</p>
          )}
          {detail && (
            <ProjectTabs
              detail={detail}
              ongletInitial={onglet}
              onChange={fiche.reload}
              enregistrerFiche={fiche.enregistrerFiche}
              enregistrerDescription={fiche.enregistrerDescription}
              changerPhase={fiche.changerPhase}
              changerCaracteristiques={fiche.changerCaracteristiques}
              ajouterLien={fiche.ajouterLien}
              retirerLien={fiche.retirerLien}
              // The panel stays open after archiving, even though the mission
              // leaves the list behind: closing it on an unlucky click would
              // leave no way back, the row having gone from the reference
              // list. The banner and « Desarchiver » keep the return
              // within reach.
              archiver={fiche.archiver}
              desarchiver={fiche.desarchiver}
            />
          )}
        </div>
      </aside>
    </>
  );
}
