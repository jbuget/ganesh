"use client";

import { SmilePlus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Reaction, UpdateReactionResponse } from "@/lib/api/generated/model";
import { glyphOf, labelOf, REACTIONS, whoReacted } from "@/lib/reactions";
import { useCursorTooltip } from "@/lib/use-cursor-tooltip";

interface UpdateReactionsProps {
  reactions: UpdateReactionResponse[];
  /**
   * Leaves a sign, or takes it back. The second argument says which of the
   * two: the bar knows what the reader already left, the caller does not have
   * to work it out again.
   */
  onToggle: (reaction: Reaction, leaving: boolean) => void;
  /**
   * Whether the reader may leave a sign of their own.
   *
   * The signs already left still show: who answered « lu » is part of the
   * thread, and a guest reads the thread.
   */
  editable?: boolean;
}

/**
 * The signs left under an update, and the way to leave one.
 *
 * A reaction is the cheapest thing one can say: it answers « lu », « d'accord »
 * or « bravo » without writing a line, and without ringing anywhere. The bar
 * shows only the signs somebody actually left — an empty row of eight faces
 * under every message would say nothing and cost the thread its calm.
 */
export function UpdateReactions({
  reactions,
  onToggle,
  editable = true,
}: UpdateReactionsProps) {
  const [picking, setPicking] = useState(false);
  // One bubble for the whole bar, the picker included: the content is given on
  // hover, and the native tooltip arrives a second too late to be read while
  // running along a row of signs.
  const { tooltip, follow, leave } = useCursorTooltip();
  // What the reader left, not what the thread left: picking a sign one has
  // already given is how one takes it back.
  const mine = new Set(
    reactions.filter((one) => one.is_mine).map((one) => one.reaction),
  );

  return (
    <div className="mt-2 flex flex-wrap items-center gap-1">
      {reactions.map((one) => {
        const says = `${labelOf(one.reaction)} : ${whoReacted(one.people)}`;
        return (
          <button
            key={one.reaction}
            type="button"
            aria-pressed={one.is_mine}
            aria-label={says}
            disabled={!editable}
            onMouseMove={(event) => follow(event, says)}
            onMouseLeave={leave}
            onClick={() => onToggle(one.reaction, !one.is_mine)}
            className={`inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-xs tabular-nums transition-colors ${
              editable ? "cursor-pointer" : ""
            } ${
              one.is_mine
                ? "border-slate-500 bg-slate-100 text-slate-800"
                : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span aria-hidden>{glyphOf(one.reaction)}</span>
            {one.people.length}
          </button>
        );
      })}

      {editable && (
        <Popover open={picking} onOpenChange={setPicking}>
          <PopoverTrigger
            aria-label="Réagir"
            className="inline-flex cursor-pointer items-center rounded-full border border-slate-300 bg-white p-1 text-slate-400 transition-colors hover:bg-slate-50 hover:text-slate-600"
          >
            <SmilePlus className="size-3.5" aria-hidden />
          </PopoverTrigger>
          <PopoverContent className="w-auto flex-row gap-0.5 p-1">
            {REACTIONS.map(({ reaction, glyph, label }) => (
              <button
                key={reaction}
                type="button"
                aria-label={label}
                onMouseMove={(event) => follow(event, label)}
                onMouseLeave={leave}
                onClick={() => {
                  onToggle(reaction, !mine.has(reaction));
                  setPicking(false);
                }}
                className="cursor-pointer rounded p-1 text-base transition-colors hover:bg-slate-100"
              >
                <span aria-hidden>{glyph}</span>
              </button>
            ))}
          </PopoverContent>
        </Popover>
      )}

      {tooltip}
    </div>
  );
}
