"use client";

import { GripVertical } from "lucide-react";
import Link from "next/link";

import { IntervenantsPicker } from "@/components/atoms/IntervenantsPicker";
import { MemberAvatars } from "@/components/atoms/MemberAvatars";
import type { BoardCardResponse } from "@/lib/api/generated/model";
import { avancement, categorie } from "@/lib/board";
import { formatJoursDecimal } from "@/lib/dates";

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
  /** Recharge le tableau apres un changement d'intervenants. */
  onIntervenantsChange?: () => void | Promise<void>;
}

/** Une mission sur le tableau de bord. */
export function ProjectCard({
  carte,
  poignee,
  enDeplacement,
  onIntervenantsChange,
}: ProjectCardProps) {
  const { project } = carte;
  const axe = categorie(project.categorie);
  const etat = avancement(carte.consomme_j, project.estime_j);

  return (
    <article
      className={[
        "group rounded-lg border bg-white p-3 shadow-xs transition-shadow",
        enDeplacement
          ? "border-sky-400 shadow-lg"
          : "border-slate-300 hover:border-slate-500 hover:shadow-sm",
      ].join(" ")}
    >
      <div className="flex items-start gap-1.5">
        <h3 className="min-w-0 flex-1 text-sm font-medium text-slate-900">
          {/*
            Le lien porte sur le titre seul, non sur la carte : celle-ci se
            saisit pour la deplacer, et un clic relache apres un glissement ne
            doit pas ouvrir une fiche.
          */}
          {enDeplacement ? (
            project.label
          ) : (
            <Link href={`/projets/${project.id}`} className="hover:underline">
              {project.label}
            </Link>
          )}
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
          ? `${formatJoursDecimal(carte.consomme_j)}/${project.estime_j} jrs. estimés`
          : `${formatJoursDecimal(carte.consomme_j)} jrs. consommés`}
      </p>

      {/*
        La copie qui suit le curseur n'est pas interactive : sans selecteur, un
        clic amorce dessus ne pourrait pas ouvrir de menu en plein glissement.
      */}
      <div className="mt-2.5">
        {enDeplacement || !onIntervenantsChange ? (
          <MemberAvatars membres={carte.intervenants} />
        ) : (
          <IntervenantsPicker
            projectId={project.id}
            intervenants={carte.intervenants}
            onChange={onIntervenantsChange}
          />
        )}
      </div>
    </article>
  );
}
