"use client";

import {
  CornerDownRight,
  GripVertical,
  MessageCircle,
  SquareStack,
} from "lucide-react";

import { CardCounter } from "@/components/atoms/CardCounter";
import { ContributorsPicker } from "@/components/atoms/ContributorsPicker";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { MemberAvatars } from "@/components/atoms/MemberAvatars";
import type { BoardCardResponse } from "@/lib/api/generated/model";
import { progress } from "@/lib/board";
import { formatDecimalDays } from "@/lib/dates";
import { depuis } from "@/lib/relative-dates";

/** Teinte du rapport consomme/estime selon l'etat d'avancement. */
const SHADES: Record<ReturnType<typeof progress>, string> = {
  "sans-estime": "text-slate-500",
  "en-cours": "text-slate-600",
  proche: "text-amber-700",
  depasse: "text-red-700",
};

interface ProjectCardProps {
  card: BoardCardResponse;
  /** Freezes the reference time: without it, server and client would diverge. */
  maintenant: Date;
  /**
   * Drag handle, provided by the sorting layer. `null` shows none: a card that
   * cannot be moved must not carry the sign of one.
   */
  handle?: React.ReactNode | null;
  isDragging?: boolean;
  /** Reloads the board after a change of contributors. */
  onIntervenantsChange?: () => void | Promise<void>;
  /** Ouvre la mission a cote du tableau. */
  onOpen?: (projectId: number) => void;
}

/** A mission on the board. */
export function ProjectCard({
  card,
  maintenant,
  handle,
  isDragging,
  onIntervenantsChange,
  onOpen,
}: ProjectCardProps) {
  const { project, parent } = card;
  const archivee = !project.is_active;
  const state = progress(card.consumed_days, project.estimated_days);
  const derniere = card.latest_update;

  // The latest message in full and formatted, as in the reference list: the
  // card says how many messages the thread carries, the preview says whether
  // it needs opening.
  const apercu = derniere && (
    <>
      {/* The rule separates the signature from the words: without it, the first
          line of the message reads as the continuation of the header. Negative
          margins carry it to the edges of the bubble, whose padding it
          crosses. */}
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
    <article
      // The whole card opens the mission, not its title alone: it is the card
      // the eye aims at. The controls it carries — handle, contributor avatars
      // — keep their click, hence the filter on buttons.
      onClick={(event) => {
        if (!onOpen || isDragging) return;
        if ((event.target as HTMLElement).closest("button")) return;
        onOpen(project.id);
      }}
      className={[
        "group rounded-lg border p-3 shadow-xs transition-shadow",
        // An archived mission is no longer steered: it reads set back, so that
        // a board mixing both can be scanned without confusing what is running
        // with what has been put away.
        archivee ? "bg-slate-50" : "bg-white",
        onOpen && !isDragging ? "cursor-pointer" : "",
        isDragging
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
            The link is on the title alone, not on the card: the card is
            grabbed to move it, and a click released after a drag must not open
            a sheet.
          */}
          {isDragging || !onOpen ? (
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
        {handle === undefined ? (
          <GripVertical className="size-4 shrink-0 text-slate-300" aria-hidden />
        ) : (
          handle
        )}
      </div>

      {/*
        What a work package belongs to reads under its title: on the board, a
        sub-project card says nothing of its project, and the label alone is
        not always enough to guess it.
      */}
      {parent && (
        <p className="mt-1 flex min-w-0 items-center gap-1 text-xs text-slate-500">
          <CornerDownRight className="size-3 shrink-0" aria-hidden />
          {isDragging || !onOpen ? (
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

      <p className={`mt-2.5 text-xs tabular-nums ${SHADES[state]}`}>
        {project.estimated_days
          ? `${formatDecimalDays(card.consumed_days)}/${project.estimated_days} jrs. estimés`
          : `${formatDecimalDays(card.consumed_days)} jrs. consommés`}
      </p>

      {/*
        The card footer: who looks after the mission on the left, what it
        carries on the right — its thread, its work packages. Both fit on one
        line: they answer the same question, what orbits the mission, and two
        separate lines would stretch the card without saying more.

        Each number precedes its icon, hence the wide gap between the two
        counts: closer together, a number would read as the count of the icon
        before it, all the more when the one beside it counts nothing.
      */}
      <div className="mt-2.5 flex items-center gap-2">
        {/*
          The copy following the cursor is not interactive: without a picker, a
          click started on it could not open a menu mid-drag.
        */}
        <div className="min-w-0 flex-1">
          {isDragging || !onIntervenantsChange ? (
            <MemberAvatars members={card.contributors} />
          ) : (
            <ContributorsPicker
              projectId={project.id}
              contributors={card.contributors}
              onChange={onIntervenantsChange}
            />
          )}
        </div>

        <div className="flex shrink-0 items-center gap-5">
          <CardCounter
            icon={MessageCircle}
            count={card.comments}
            label={["commentaire", "commentaires"]}
            empty="Aucun commentaire"
            // The copy following the cursor announces nothing: a bubble opened
            // under the card mid-drag would hide where it lands.
            apercu={isDragging ? undefined : apercu}
          />
          <CardCounter
            icon={SquareStack}
            count={card.sub_projects}
            label={["sous-projet", "sous-projets"]}
            empty="Aucun sous-projet"
          />
        </div>
      </div>
    </article>
  );
}
