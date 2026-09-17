"use client";

import { ChevronRight } from "lucide-react";

import { CategoryMark } from "@/components/atoms/CategoryMark";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { MemberAvatars } from "@/components/atoms/MemberAvatars";
import { PriorityMark } from "@/components/atoms/PriorityMark";
import { UpdatesCounter } from "@/components/atoms/UpdatesCounter";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { phaseLabel, phaseDot } from "@/lib/board";
import { depuis } from "@/lib/dates-relatives";

interface MissionRowProps {
  mission: ProjectListItemResponse;
  /** Un lot se decale sous son projet, pour que la hierarchie se lise. */
  estLot?: boolean;
  /** Combien de sous-projets la mission porte : aucun, rien a plier. */
  lots?: number;
  /** Si ses sous-projets sont visibles. Replie par defaut. */
  deplie?: boolean;
  /** Montre ou cache les sous-projets. */
  onBasculer?: () => void;
  /** Fige l'heure de reference : sans cela, serveur et client divergeraient. */
  maintenant: Date;
  onOpen: () => void;
  /** Ouvre la mission sur son fil, la ou l'apercu s'arrete. */
  onOpenFil: () => void;
}

/**
 * Une mission du referentiel, colonne par colonne.
 *
 * La ligne ne porte toujours aucune action : elle montre de quoi comparer deux
 * missions du regard — ou elles en sont, ce qu'elles pesent, qui s'en occupe —
 * et tout ce qui se modifie continue de se faire dans le panneau, d'un seul
 * endroit.
 */
export function MissionRow({
  mission,
  estLot = false,
  lots = 0,
  deplie = false,
  onBasculer,
  maintenant,
  onOpen,
  onOpenFil,
}: MissionRowProps) {
  const { project } = mission;
  const derniere = mission.latest_update;

  // Le dernier message en entier et mis en forme, comme il se lit dans le fil :
  // un apercu tronque obligerait a ouvrir le panneau pour la fin d'une phrase.
  const apercu = derniere && (
    <>
      {/* Le trait separe la signature du propos : sans lui, la premiere ligne
          du message se lit comme la suite de l'entete. Les marges negatives le
          menent aux bords de la bulle, dont il traverse le rembourrage. */}
      <p className="-mx-3 mb-2 border-b border-slate-200 px-3 pb-2 text-xs text-slate-500">
        <span className="font-medium text-slate-700">
          {derniere.author.display_name}
        </span>{" "}
        · {depuis(derniere.published_at, maintenant)}
      </p>
      <MarkdownView body={derniere.body} />
    </>
  );

  return (
    <TableRow onClick={onOpen} className="cursor-pointer">
      <TableCell className={estLot ? "pl-14" : ""}>
        <span className="flex items-center gap-2">
          {/* Le crochet rattache le lot a son projet : sans lui, l'indentation
              seule se perd des qu'une ligne longue passe a la suivante. */}
          {estLot && (
            <span aria-hidden className="-ml-4 text-slate-300">
              └
            </span>
          )}

          {/* Un referentiel de soixante lignes se parcourt mal deplie en
              entier : le chevron rend le detail d'un projet a la demande. La
              gouttiere reste meme sans sous-projet, sinon les noms ne
              tomberaient plus sur la meme verticale d'une ligne a l'autre. */}
          {!estLot &&
            (lots > 0 ? (
              <button
                type="button"
                aria-expanded={deplie}
                aria-label={`${deplie ? "Masquer" : "Afficher"} ${
                  lots > 1 ? `les ${lots} sous-projets` : "le sous-projet"
                } de ${project.label}`}
                // La ligne entiere ouvre la mission : sans arret, replier
                // ouvrirait le panneau par la meme occasion.
                onClick={(event) => {
                  event.stopPropagation();
                  onBasculer?.();
                }}
                className="cursor-pointer rounded p-0.5 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
              >
                <ChevronRight
                  aria-hidden
                  className={`size-4 transition-transform ${deplie ? "rotate-90" : ""}`}
                />
              </button>
            ) : (
              <span aria-hidden className="size-5 shrink-0" />
            ))}
          <button
            type="button"
            // La ligne entiere reagit a la souris ; ce bouton donne la meme
            // ouverture au clavier, sans declencher deux fois l'ouverture.
            onClick={(event) => {
              event.stopPropagation();
              onOpen();
            }}
            className={[
              "cursor-pointer text-left",
              estLot ? "text-slate-600" : "font-medium text-slate-800",
            ].join(" ")}
          >
            {project.label}
          </button>
        </span>
      </TableCell>

      {/* Le fil se lit contre le nom de la mission, dont il dit l'activite :
          plus loin, on ne saurait plus de quelle ligne il parle. L'icone dit
          deja ce que le nombre compte, d'ou l'en-tete vide. */}
      <TableCell className="w-12 text-right">
        <UpdatesCounter count={mission.comments} apercu={apercu} onOpen={onOpenFil} />
      </TableCell>

      <TableCell>
        {project.status && (
          <span className="flex items-center gap-1.5 text-slate-700">
            <span
              aria-hidden
              className={`size-2.5 shrink-0 rounded-full ${phaseDot(project.status)}`}
            />
            {phaseLabel(project.status)}
          </span>
        )}
      </TableCell>

      {/* La priorite suit la phase, comme dans la fiche : ou en est la mission,
          puis ce qu'elle doit passer avant. */}
      <TableCell>
        <PriorityMark value={project.priority} />
      </TableCell>

      <TableCell>
        <CategoryMark value={project.category} />
      </TableCell>

      <TableCell className="text-right tabular-nums text-slate-600">
        {project.estimated_days != null && `${project.estimated_days} jrs.`}
      </TableCell>

      {/* Le realise s'ecrit a cote de l'estime pour qu'on les compare d'un
          coup d'oeil. Un zero n'est pas une valeur a lire : une mission ou
          personne n'a encore declare reste vide. */}
      <TableCell className="text-right tabular-nums text-slate-600">
        {mission.delivered_days > 0 && `${mission.delivered_days} jrs.`}
      </TableCell>

      <TableCell>
        <MemberAvatars members={mission.leads} />
      </TableCell>

      <TableCell>
        <MemberAvatars members={mission.contributors} />
      </TableCell>
    </TableRow>
  );
}
