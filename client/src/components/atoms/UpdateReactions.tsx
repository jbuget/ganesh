"use client";

import { SmilePlus } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Reaction, UpdateReactionResponse } from "@/lib/api/generated/model";
import { glyphOf, labelOf, REACTIONS, whoReacted } from "@/lib/reactions";

interface UpdateReactionsProps {
  reactions: UpdateReactionResponse[];
  /**
   * Leaves a sign, or takes it back. The second argument says which of the
   * two: the bar knows what the reader already left, the caller does not have
   * to work it out again.
   */
  onToggle: (reaction: Reaction, leaving: boolean) => void;
}

/**
 * The signs left under an update, and the way to leave one.
 *
 * A reaction is the cheapest thing one can say: it answers « lu », « d'accord »
 * or « bravo » without writing a line, and without ringing anywhere. The bar
 * shows only the signs somebody actually left — an empty row of eight faces
 * under every message would say nothing and cost the thread its calm.
 */
export function UpdateReactions({ reactions, onToggle }: UpdateReactionsProps) {
  const [picking, setPicking] = useState(false);
  // What the reader left, not what the thread left: picking a sign one has
  // already given is how one takes it back.
  const mine = new Set(
    reactions.filter((one) => one.is_mine).map((one) => one.reaction),
  );

  return (
    <div className="mt-2 flex flex-wrap items-center gap-1">
      {reactions.map((one) => (
        <button
          key={one.reaction}
          type="button"
          aria-pressed={one.is_mine}
          aria-label={`${labelOf(one.reaction)} : ${whoReacted(one.people)}`}
          title={`${labelOf(one.reaction)} : ${whoReacted(one.people)}`}
          onClick={() => onToggle(one.reaction, !one.is_mine)}
          className={`inline-flex cursor-pointer items-center gap-1 rounded-full border px-1.5 py-0.5 text-xs tabular-nums transition-colors ${
            one.is_mine
              ? "border-slate-500 bg-slate-100 text-slate-800"
              : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
          }`}
        >
          <span aria-hidden>{glyphOf(one.reaction)}</span>
          {one.people.length}
        </button>
      ))}

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
              title={label}
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
    </div>
  );
}
