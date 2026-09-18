"use client";

import {
  CornerDownRight,
  GripVertical,
  MessageCircle,
  SquareStack,
} from "lucide-react";

import { CardCounter } from "@/components/atoms/CardCounter";
import { IntervenantsPicker } from "@/components/atoms/IntervenantsPicker";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { MemberAvatars } from "@/components/atoms/MemberAvatars";
import type { BoardCardResponse } from "@/lib/api/generated/model";
import { avancement } from "@/lib/board";
import { formatJoursDecimal } from "@/lib/dates";
import { depuis } from "@/lib/dates-relatives";

/** Teinte du rapport consomme/estime selon l'etat d'avancement. */
const TEINTES: Record<ReturnType<typeof avancement>, string> = {
  "sans-estime": "text-slate-500",
  "en-cours": "text-slate-600",
  proche: "text-amber-700",
  depasse: "text-red-700",
};

interface ProjectCardProps {
  carte: BoardCardResponse;
  /** Fige l'heure de reference : sans cela, serveur et client divergeraient. */
  maintenant: Date;
  /**
   * Poignee de glissement, fournie par la couche de tri. `null` n'en montre
   * aucune : une carte qu'on ne peut pas deplacer ne doit pas en porter le
   * signe.
   */
  poignee?: React.ReactNode | null;
  enDeplacement?: boolean;
  /** Recharge le tableau apres un changement d'intervenants. */
  onIntervenantsChange?: () => void | Promise<void>;
  /** Ouvre la mission a cote du tableau. */
  onOpen?: (projectId: number) => void;
}

/** Une mission sur le tableau de bord. */
export function ProjectCard({
  carte,
  maintenant,
  poignee,
  enDeplacement,
  onIntervenantsChange,
  onOpen,
}: ProjectCardProps) {
  const { project, parent } = carte;
  const archivee = !project.actif;
  const etat = avancement(carte.consomme_j, project.estime_j);
  const derniere = carte.derniere_maj;

  // Le dernier message en entier et mis en forme, comme dans le referentiel :
  // la carte dit combien de messages porte le fil, l'apercu dit s'il faut
  // l'ouvrir.
  const apercu = derniere && (
    <>
      {/* Le trait separe la signature du propos : sans lui, la premiere ligne
          du message se lit comme la suite de l'entete. Les marges negatives le
          menent aux bords de la bulle, dont il traverse le rembourrage. */}
      <p className="-mx-3 mb-2 border-b border-slate-200 px-3 pb-2 text-xs text-slate-500">
        <span className="font-medium text-slate-700">
          {derniere.author.display_name}
        </span>{" "}
        · {depuis(derniere.publiee_le, maintenant)}
      </p>
      <MarkdownView texte={derniere.texte} />
    </>
  );

  return (
    <article
      // Toute la carte ouvre la mission, et non son seul titre : c'est la carte
      // qu'on vise du regard. Les controles qu'elle porte — poignee, pastilles
      // d'intervenants — gardent leur clic, d'ou le filtre sur les boutons.
      onClick={(event) => {
        if (!onOpen || enDeplacement) return;
        if ((event.target as HTMLElement).closest("button")) return;
        onOpen(project.id);
      }}
      className={[
        "group rounded-lg border p-3 shadow-xs transition-shadow",
        // Une archivee ne se pilote plus : elle se lit en retrait, pour qu'un
        // tableau melant les deux se parcoure sans confondre ce qui tourne et
        // ce qui est range.
        archivee ? "bg-slate-50" : "bg-white",
        onOpen && !enDeplacement ? "cursor-pointer" : "",
        enDeplacement
          ? "border-sky-400 shadow-lg"
          : "border-slate-300 hover:border-slate-500 hover:shadow-sm",
      ].join(" ")}
    >
      <div className="flex items-start gap-1.5">
        <h3
          className={`min-w-0 flex-1 text-sm font-medium ${
            archivee ? "text-slate-500" : "text-slate-900"
          }`}
        >
          {/*
            Le lien porte sur le titre seul, non sur la carte : celle-ci se
            saisit pour la deplacer, et un clic relache apres un glissement ne
            doit pas ouvrir une fiche.
          */}
          {enDeplacement || !onOpen ? (
            project.label
          ) : (
            <button
              type="button"
              onClick={() => onOpen(project.id)}
              className="cursor-pointer text-left hover:underline"
            >
              {project.label}
            </button>
          )}
        </h3>
        {poignee === undefined ? (
          <GripVertical className="size-4 shrink-0 text-slate-300" aria-hidden />
        ) : (
          poignee
        )}
      </div>

      {/*
        D'ou releve un lot se lit sous son titre : sur le tableau, une carte de
        sous-projet ne dit rien de son projet, et l'intitule seul ne suffit pas
        toujours a le deviner.
      */}
      {parent && (
        <p className="mt-1 flex min-w-0 items-center gap-1 text-xs text-slate-500">
          <CornerDownRight className="size-3 shrink-0" aria-hidden />
          {enDeplacement || !onOpen ? (
            <span className="truncate">{parent.label}</span>
          ) : (
            <button
              type="button"
              onClick={() => onOpen(parent.id)}
              className="cursor-pointer truncate text-left hover:text-slate-700 hover:underline"
            >
              {parent.label}
            </button>
          )}
        </p>
      )}

      {archivee && (
        <span className="mt-2 mr-1 inline-block rounded bg-slate-200 px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
          Archivée
        </span>
      )}

      <p className={`mt-2.5 text-xs tabular-nums ${TEINTES[etat]}`}>
        {project.estime_j
          ? `${formatJoursDecimal(carte.consomme_j)}/${project.estime_j} jrs. estimés`
          : `${formatJoursDecimal(carte.consomme_j)} jrs. consommés`}
      </p>

      {/*
        Le pied de carte : qui s'occupe de la mission a gauche, ce qu'elle
        porte a droite — son fil, ses lots. Les deux tiennent sur une seule
        ligne : ils repondent a la meme question, ce qui gravite autour de la
        mission, et deux lignes distinctes etiraient la carte sans rien dire de
        plus.

        Chaque nombre precede son icone, d'ou l'ecart large entre les deux
        decomptes : plus serres, un nombre se lirait comme le compte de l'icone
        qui le precede, surtout quand celle d'a cote ne compte rien.
      */}
      <div className="mt-2.5 flex items-center gap-2">
        {/*
          La copie qui suit le curseur n'est pas interactive : sans selecteur,
          un clic amorce dessus ne pourrait pas ouvrir de menu en plein
          glissement.
        */}
        <div className="min-w-0 flex-1">
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

        <div className="flex shrink-0 items-center gap-5">
          <CardCounter
            icone={MessageCircle}
            nombre={carte.commentaires}
            libelle={["commentaire", "commentaires"]}
            vide="Aucun commentaire"
            // La copie qui suit le curseur n'annonce rien : une bulle ouverte
            // sous la carte en plein deplacement masquerait la ou elle tombe.
            apercu={enDeplacement ? undefined : apercu}
          />
          <CardCounter
            icone={SquareStack}
            nombre={carte.sous_projets}
            libelle={["sous-projet", "sous-projets"]}
            vide="Aucun sous-projet"
          />
        </div>
      </div>
    </article>
  );
}
