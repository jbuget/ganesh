"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { ProjectTabs } from "@/components/organisms/ProjectTabs";
import { libellePhase, pastillePhase } from "@/lib/board";
import { formatJoursDecimal } from "@/lib/dates";
import { useProjectDetail } from "@/lib/use-project-detail";

interface ProjectDetailPageProps {
  projectId: number;
}

/**
 * La mission en pleine page.
 *
 * Meme contenu que le panneau lateral, au large : pour lire une fiche service
 * ou parcourir un journal, l'espace compte.
 */
export function ProjectDetailPage({ projectId }: ProjectDetailPageProps) {
  const fiche = useProjectDetail(projectId);
  const detail = fiche.detail;

  if (fiche.introuvable) {
    return (
      <main className="max-w-[900px] p-6">
        <p className="text-sm text-slate-500">Cette mission n&apos;existe pas.</p>
      </main>
    );
  }

  if (!detail) {
    return (
      <main className="max-w-[900px] p-6">
        <p className="text-sm text-slate-500">Chargement…</p>
      </main>
    );
  }

  const { project } = detail;

  return (
    <main className="max-w-[900px] p-6">
      <Link
        href="/kanban"
        className="mb-4 inline-flex cursor-pointer items-center gap-1.5 text-sm text-slate-500 transition-colors hover:text-slate-800"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Kanban
      </Link>

      <header className="mb-6">
        <h1 className="text-xl font-semibold">{project.label}</h1>
        <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
          {project.statut && (
            <span className="flex items-center gap-1.5">
              <span
                aria-hidden
                className={`size-2.5 rounded-full ${pastillePhase(project.statut)}`}
              />
              {libellePhase(project.statut)}
            </span>
          )}
          <span>
            {formatJoursDecimal(detail.consomme_j)}
            {project.estime_j ? `/${project.estime_j}` : ""} jrs.
            {project.estime_j ? " estimés" : " consommés"}
          </span>
        </p>
      </header>

      <ProjectTabs
        detail={detail}
        onChange={fiche.recharger}
        enregistrerFiche={fiche.enregistrerFiche}
        enregistrerDescription={fiche.enregistrerDescription}
        changerPhase={fiche.changerPhase}
        changerCaracteristiques={fiche.changerCaracteristiques}
      />
    </main>
  );
}
