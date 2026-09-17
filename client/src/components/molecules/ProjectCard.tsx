"use client";

import { GripVertical } from "lucide-react";

import { MemberAvatars } from "@/components/atoms/MemberAvatars";
import type { BoardCardResponse } from "@/lib/api/generated/model";
import { avancement, categorie } from "@/lib/board";
import { formatTotal } from "@/lib/dates";

/** Teinte du rapport consomme/estime selon l'etat d'avancement. */
const TEINTES: Record<ReturnType<typeof avancement>, string> = {
  "sans-estime": "text-slate-500",
  "en-cours": "text-slate-600",
  proche: "text-amber-700",
  depasse: "text-red-700",
};

interface ProjectCardProps {
  carte: BoardCardResponse;
  /** Poignee de glissement, fournie par la couche de tri. */
  poignee?: React.ReactNode;
  enDeplacement?: boolean;
}

/** Une mission sur le tableau de bord. */
export function ProjectCard({ carte, poignee, enDeplacement }: ProjectCardProps) {
  const { project } = carte;
  const axe = categorie(project.categorie);
  const etat = avancement(carte.consomme_j, project.estime_j);

  return (
    <article
      className={[
        "group rounded-lg border bg-white p-3 shadow-xs transition-shadow",
        enDeplacement
          ? "border-sky-400 shadow-lg"
          : "border-slate-200 hover:border-slate-500 hover:shadow-sm",
      ].join(" ")}
    >
      <div className="flex items-start gap-1.5">
        <h3 className="min-w-0 flex-1 text-sm font-medium text-slate-900">
          {project.label}
        </h3>
        {poignee ?? (
          <GripVertical className="size-4 shrink-0 text-slate-300" aria-hidden />
        )}
      </div>

      {axe && (
        <span
          className={`mt-2 inline-block rounded px-1.5 py-0.5 text-[11px] font-medium ${axe.classe}`}
        >
          {axe.libelle}
        </span>
      )}

      <p className={`mt-2.5 text-xs tabular-nums ${TEINTES[etat]}`}>
        {project.estime_j
          ? `${formatTotal(carte.consomme_j)}/${project.estime_j} jrs. estimés`
          : `${formatTotal(carte.consomme_j)} jrs. consommés`}
      </p>

      {carte.collaborateurs.length > 0 && (
        <div className="mt-2.5">
          <MemberAvatars membres={carte.collaborateurs} />
        </div>
      )}
    </article>
  );
}
