"use client";

import { CornerDownRight, MessageCircle, SquareStack } from "lucide-react";

import { CardCounter } from "@/components/atoms/CardCounter";
import { ContributorsPicker } from "@/components/atoms/ContributorsPicker";
import { FollowMark } from "@/components/atoms/FollowMark";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { MemberAvatars } from "@/components/atoms/MemberAvatars";
import type { BoardCardResponse } from "@/lib/api/generated/model";
import { progress } from "@/lib/board";
import { formatDecimalDays } from "@/lib/dates";
import { since } from "@/lib/relative-dates";

/** Shade of the consumed/estimated ratio, by how far along it is. */
const SHADES: Record<ReturnType<typeof progress>, string> = {
  "no-estimate": "text-slate-500",
  ongoing: "text-slate-600",
  close: "text-amber-700",
  over: "text-red-700",
};

interface ProjectCardProps {
  card: BoardCardResponse;
  /** Freezes the reference time: without it, server and client would diverge. */
  now: Date;
  /**
   * The keyboard's way to move the card, provided by the sorting layer. The
   * pointer grabs the card itself, so the card draws no grip.
   */
  handle?: React.ReactNode;
  isDragging?: boolean;
  /** Reloads the board after a change of contributors. */
  onContributorsChange?: () => void | Promise<void>;
  /** Opens the mission beside the board. */
  onOpen?: (projectId: number) => void;
  /**
   * Opens the mission on its thread, with the composer ready.
   *
   * The bubble reads the thread, so it leads there: one clicks it to answer.
   * The rest of the card opens the sheet, as before.
   */
  onOpenThread?: (projectId: number) => void;
  /**
   * Raises or lowers the mark the team follows the mission by. Absent on the
   * copy that follows the pointer, which only shows the mark.
   */
  onFollowChange?: (projectId: number, following: boolean) => void;
}

/** A mission on the board. */
export function ProjectCard({
  card,
  now,
  handle,
  isDragging,
  onContributorsChange,
  onOpen,
  onOpenThread,
  onFollowChange,
}: ProjectCardProps) {
  const { project, parent } = card;
  const archived = !project.is_active;
  // The estimate only covers the construction: a service kept alive for two
  // years is not late because it is still running.
  const state = progress(card.build_days, project.estimated_days);
  const latest = card.latest_update;
  // Nothing opens from the copy following the cursor: a click released after
  // a drag must not open a panel.
  const thread = isDragging ? undefined : onOpenThread;

  // The latest message in full and formatted, as in the reference list: the
  // card says how many messages the thread carries, the preview says whether
  // it needs opening.
  const preview = latest && (
    <>
      {/* The rule separates the signature from the words: without it, the first
          line of the message reads as the continuation of the header. Negative
          margins carry it to the edges of the bubble, whose padding it
          crosses. */}
      <p className="-mx-3 mb-2 border-b border-slate-200 px-3 pb-2 text-xs text-slate-500">
        <span className="font-medium text-slate-700">{latest.author.display_name}</span>{" "}
        · {since(latest.published_at, now)}
      </p>
      <MarkdownView body={latest.body} />
    </>
  );

  return (
    <article
      // The whole card opens the mission, not its title alone: it is the card
      // the eye aims at. The controls it carries — title, contributor avatars,
      // follow mark — keep their click, hence the filter on buttons.
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
        archived ? "bg-slate-50" : "bg-white",
        onOpen && !isDragging ? "cursor-pointer" : "",
        isDragging
          ? "border-sky-400 shadow-lg"
          : "border-slate-300 hover:border-slate-500 hover:shadow-sm",
      ].join(" ")}
    >
      {handle}
      <div className="flex items-start gap-1.5">
        <h3
          className={`min-w-0 flex-1 text-sm font-medium ${
            archived ? "text-slate-500" : "text-slate-900"
          }`}
        >
          {/*
            A button as well as the card: it is what the keyboard reaches to
            open the mission, the card itself taking no focus.
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
        {/* Small, in the top right corner rather than after the words: the
            title is a button, which lays out as a block once it wraps, and a
            mark set after it would drop to a line of its own. Followed, it
            stays; otherwise it only comes up under the cursor — a board of
            thirty cards each carrying an empty flag would read as thirty
            marks. */}
        <FollowMark
          followed={project.is_followed}
          onToggle={
            onFollowChange && !isDragging
              ? () => onFollowChange(project.id, !project.is_followed)
              : undefined
          }
          className={`shrink-0 px-0.5 [&_svg]:size-3 ${
            project.is_followed
              ? ""
              : "opacity-0 group-hover:opacity-100 focus:opacity-100"
          }`}
        />
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

      {archived && (
        <span className="mt-2 mr-1 inline-block rounded bg-slate-200 px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
          Archivée
        </span>
      )}

      <p className={`mt-2.5 text-xs tabular-nums ${SHADES[state]}`}>
        {project.estimated_days
          ? `${formatDecimalDays(card.build_days)}/${formatDecimalDays(project.estimated_days)} jrs. estimés`
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
          {isDragging || !onContributorsChange ? (
            <MemberAvatars members={card.contributors} />
          ) : (
            <ContributorsPicker
              projectId={project.id}
              contributors={card.contributors}
              onChange={onContributorsChange}
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
            preview={isDragging ? undefined : preview}
            onOpen={thread && (() => thread(project.id))}
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
