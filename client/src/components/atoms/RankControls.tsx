"use client";

import { ChevronDown, ChevronUp, ChevronsUp } from "lucide-react";

interface RankControlsProps {
  /** Named in the labels, so each control says what it acts on. */
  label: string;
  isFirst: boolean;
  isLast: boolean;
  onTop: () => void;
  onUp: () => void;
  onDown: () => void;
}

/**
 * Moving a mission up or down the queue, by clicking.
 *
 * Dragging alone was not enough: a grip handle announces nothing, and getting
 * a mission from the fortieth rank to the first one row at a time is not a
 * tool, it is a chore. Hence « passer en tête », which does it in one click.
 *
 * The buttons show at all times rather than on hover: what one cannot see one
 * does not use, and this is the screen's main lever.
 */
export function RankControls({
  label,
  isFirst,
  isLast,
  onTop,
  onUp,
  onDown,
}: RankControlsProps) {
  const style =
    "cursor-pointer rounded p-0.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:bg-transparent";

  return (
    <span className="flex items-center">
      <button
        type="button"
        disabled={isFirst}
        onClick={onTop}
        title={`Passer « ${label} » en tête`}
        aria-label={`Passer ${label} en tête`}
        className={style}
      >
        <ChevronsUp className="size-4" aria-hidden />
      </button>
      <button
        type="button"
        disabled={isFirst}
        onClick={onUp}
        title={`Monter « ${label} »`}
        aria-label={`Monter ${label}`}
        className={style}
      >
        <ChevronUp className="size-4" aria-hidden />
      </button>
      <button
        type="button"
        disabled={isLast}
        onClick={onDown}
        title={`Descendre « ${label} »`}
        aria-label={`Descendre ${label}`}
        className={style}
      >
        <ChevronDown className="size-4" aria-hidden />
      </button>
    </span>
  );
}
