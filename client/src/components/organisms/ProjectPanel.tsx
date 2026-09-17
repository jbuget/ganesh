"use client";

import { Maximize2, X } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

import { ProjectTabs } from "@/components/organisms/ProjectTabs";
import { useProjectDetail } from "@/lib/use-project-detail";

interface ProjectPanelProps {
  projectId: number;
  onClose: () => void;
}

/**
 * La mission ouverte a cote du tableau.
 *
 * Le kanban reste visible et utilisable derriere : on consulte une mission sans
 * perdre de vue la colonne d'ou elle vient, ni l'endroit ou on comptait la
 * deposer ensuite.
 */
export function ProjectPanel({ projectId, onClose }: ProjectPanelProps) {
  const fiche = useProjectDetail(projectId);
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
        Le voile ferme au clic mais ne masque pas : le tableau doit rester
        lisible, c'est tout l'interet d'un panneau plutot que d'une page.
      */}
      <div
        aria-hidden
        onClick={onClose}
        className="fixed inset-0 z-40 bg-slate-900/5"
      />

      <aside
        aria-label={detail ? detail.project.label : "Mission"}
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[34rem] flex-col border-l border-slate-300 bg-white shadow-xl"
      >
        <header className="flex items-start gap-2 border-b border-slate-200 px-5 py-4">
          <div className="min-w-0 flex-1">
            <h2 className="truncate text-base font-semibold">
              {detail?.project.label ?? "Chargement…"}
            </h2>
          </div>

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

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          {fiche.introuvable && (
            <p className="text-sm text-slate-500">Cette mission n&apos;existe pas.</p>
          )}
          {detail && (
            <ProjectTabs
              detail={detail}
              onChange={fiche.recharger}
              enregistrerFiche={fiche.enregistrerFiche}
            />
          )}
        </div>
      </aside>
    </>
  );
}
