"use client";

import { MessageCircle } from "lucide-react";

import { MemberAvatars } from "@/components/atoms/MemberAvatars";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { categorie, libellePhase, pastillePhase } from "@/lib/board";

interface MissionRowProps {
  mission: ProjectListItemResponse;
  /** Un lot se decale sous son projet, pour que la hierarchie se lise. */
  estLot?: boolean;
  onOpen: () => void;
}

/**
 * Une mission du referentiel, colonne par colonne.
 *
 * La ligne ne porte toujours aucune action : elle montre de quoi comparer deux
 * missions du regard — ou elles en sont, ce qu'elles pesent, qui s'en occupe —
 * et tout ce qui se modifie continue de se faire dans le panneau, d'un seul
 * endroit.
 */
export function MissionRow({ mission, estLot = false, onOpen }: MissionRowProps) {
  const { project } = mission;
  const axe = categorie(project.categorie);

  return (
    <TableRow onClick={onOpen} className="cursor-pointer">
      <TableCell className={estLot ? "pl-9" : ""}>
        <span className="flex items-center gap-2">
          {/* Le crochet rattache le lot a son projet : sans lui, l'indentation
              seule se perd des qu'une ligne longue passe a la suivante. */}
          {estLot && (
            <span aria-hidden className="-ml-4 text-slate-300">
              └
            </span>
          )}
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
          deja ce que le nombre compte, d'ou l'en-tete vide. Une mission sans
          mise a jour ne montre rien, comme son realise a zero : dans un
          tableau, seul ce qui se lit s'affiche. */}
      <TableCell className="w-12 text-right">
        {mission.commentaires > 0 && (
          <span
            aria-label={`${mission.commentaires} ${
              mission.commentaires > 1 ? "mises à jour" : "mise à jour"
            }`}
            className="inline-flex items-center gap-1 text-xs tabular-nums text-slate-500"
          >
            {mission.commentaires}
            <MessageCircle className="size-3.5 shrink-0" aria-hidden />
          </span>
        )}
      </TableCell>

      <TableCell>
        {project.statut && (
          <span className="flex items-center gap-1.5 text-slate-700">
            <span
              aria-hidden
              className={`size-2.5 shrink-0 rounded-full ${pastillePhase(project.statut)}`}
            />
            {libellePhase(project.statut)}
          </span>
        )}
      </TableCell>

      <TableCell>
        {axe && (
          <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${axe.classe}`}>
            {axe.libelle}
          </span>
        )}
      </TableCell>

      <TableCell className="text-right tabular-nums text-slate-600">
        {project.estime_j != null && `${project.estime_j} jrs.`}
      </TableCell>

      {/* Le realise s'ecrit a cote de l'estime pour qu'on les compare d'un
          coup d'oeil. Un zero n'est pas une valeur a lire : une mission ou
          personne n'a encore declare reste vide. */}
      <TableCell className="text-right tabular-nums text-slate-600">
        {mission.realise_j > 0 && `${mission.realise_j} jrs.`}
      </TableCell>

      <TableCell>
        <MemberAvatars membres={mission.referents} />
      </TableCell>

      <TableCell>
        <MemberAvatars membres={mission.intervenants} />
      </TableCell>
    </TableRow>
  );
}
