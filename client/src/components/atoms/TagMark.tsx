"use client";

import { Bookmark, X } from "lucide-react";

import type { TagResponse } from "@/lib/api/generated/model";
import { tagMark } from "@/lib/tag-colors";

interface TagMarkProps {
  tag: Pick<TagResponse, "name" | "color">;
  /**
   * Takes the tag off, in one click.
   *
   * Absent where the tag is only read — a row, a card: no cross is drawn.
   */
  onRemove?: () => void;
}

/**
 * Un tag posé sur un projet : une marque colorée, puis le nom en texte
 * ordinaire.
 *
 * A bookmark, where a phase's dot is round, a category's bullet square and a
 * priority a gauge: on one line, two marks of the same shape would read as the
 * same information.
 */
export function TagMark({ tag, onRemove }: TagMarkProps) {
  return (
    <span className="inline-flex max-w-full items-center gap-1.5 text-slate-700">
      {/* An icon, not a rotated box: a transform would paint over the pinned
          columns of the reference list as it scrolls. */}
      <Bookmark
        className={`size-3 shrink-0 fill-current ${tagMark(tag.color)}`}
        aria-hidden
      />
      <span className="truncate">{tag.name}</span>
      {onRemove && (
        <button
          type="button"
          aria-label={`Retirer le tag ${tag.name}`}
          onClick={onRemove}
          className="-mr-0.5 cursor-pointer rounded text-slate-400 transition-colors hover:text-slate-700"
        >
          <X className="size-3" aria-hidden />
        </button>
      )}
    </span>
  );
}
