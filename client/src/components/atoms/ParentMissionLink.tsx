"use client";

import { CornerLeftUp } from "lucide-react";
import Link from "next/link";

import type { ParentResponse } from "@/lib/api/generated/model";

interface ParentMissionLinkProps {
  parent: ParentResponse;
  /**
   * Opens the project in place. Without it the link navigates to the project's
   * own page: beside a board there is a panel to swap, on a full page there is
   * not.
   */
  onOpen?: (projectId: number) => void;
}

/**
 * The project a work package belongs to, above its title.
 *
 * A sheet opened on its own says nothing of the whole it is part of: read from
 * a link or from the thread, « Lot 1 – API » gives no clue as to which service
 * it builds. The line says it, and leads there.
 *
 * It names the tie rather than only the project — a lone name above a title
 * would read as a category. The separator is a middle dot, not « de »: the
 * label is whatever someone typed, and no preposition elides gracefully in
 * front of all of them.
 */
export function ParentMissionLink({ parent, onOpen }: ParentMissionLinkProps) {
  const content = (
    <>
      <CornerLeftUp className="size-3.5 shrink-0 text-slate-400" aria-hidden />
      <span className="shrink-0">Sous-projet</span>
      <span aria-hidden className="text-slate-300">
        ·
      </span>
      {/* Truncated, the name stays readable in full on hover: the panel is
          narrow and the reference list's labels overflow it. */}
      <span className="min-w-0 truncate font-medium text-slate-700">
        {parent.label}
      </span>
    </>
  );

  const style =
    "group -mx-1 flex max-w-full cursor-pointer items-center gap-1.5 rounded px-1 py-0.5 text-sm text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800";

  if (!onOpen) {
    return (
      <Link href={`/projects/${parent.id}`} title={parent.label} className={style}>
        {content}
      </Link>
    );
  }

  return (
    <button
      type="button"
      title={parent.label}
      onClick={() => onOpen(parent.id)}
      className={style}
    >
      {content}
    </button>
  );
}
