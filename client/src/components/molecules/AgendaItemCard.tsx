"use client";

import { ChevronDown, ChevronUp, Flag, FlagOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import type { FlaggedUpdateResponse } from "@/lib/api/generated/model";
import { renderMentions, type MentionablePerson } from "@/lib/mentions";
import { since } from "@/lib/relative-dates";

interface AgendaItemCardProps {
  item: FlaggedUpdateResponse;
  /** Freezes the reference time: without it, server and client would diverge. */
  now: Date;
  /** The register, which is what a mention in the text is read against. */
  people?: MentionablePerson[];
  /** Takes it off the agenda. Absent for a reader who may only read. */
  onClear?: () => Promise<void> | void;
}

/**
 * How much of an update an agenda shows before it is asked to show the rest.
 *
 * An agenda is a list one reads down: a single update running to three
 * screens buries the four lines under it, and the point of gathering them was
 * to see them together.
 */
const FOLDED_HEIGHT = "12rem";

/**
 * One line of the agenda: what somebody wants read out at the next revue.
 *
 * The words are the reason it is here — no motive is asked for separately,
 * because a mark on a message that already says what it says would be the
 * same sentence typed twice.
 */
export function AgendaItemCard({
  item,
  now,
  people = [],
  onClear,
}: AgendaItemCardProps) {
  const body = useRef<HTMLDivElement>(null);
  const [unfolded, setUnfolded] = useState(false);
  const [overflows, setOverflows] = useState(false);

  // Measured rather than guessed from the length of the text: what decides is
  // the height once drawn, and a table or an image counts for more than the
  // characters it costs. Followed while the ground moves, since an image is
  // only measured once it has loaded.
  useEffect(() => {
    const it = body.current;
    if (!it) return;

    const measure = () => setOverflows(it.scrollHeight > it.clientHeight + 1);
    measure();
    const watch = new ResizeObserver(measure);
    watch.observe(it);
    return () => watch.disconnect();
  }, [item.body]);

  return (
    <article className="rounded-lg border border-slate-300 bg-white p-3">
      <header className="mb-2 flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2 text-xs">
        <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
          {item.author.initials}
        </span>
        <span className="font-medium text-slate-800">{item.author.display_name}</span>
        <span className="text-slate-400">{since(item.published_at, now)}</span>

        {/* Who put it here, and since when: on an agenda read a fortnight
            later, that is what says whether the question is still open. */}
        <span className="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-800">
          <Flag className="size-3" aria-hidden />
          Signalé par {item.raised_by.display_name} · {since(item.flagged_at, now)}
        </span>

        {onClear && (
          <button
            type="button"
            onClick={() => void onClear()}
            className="ml-auto flex cursor-pointer items-center gap-1 rounded border border-slate-300 px-2 py-1 font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            <FlagOff className="size-3" aria-hidden />
            Discuté
          </button>
        )}
      </header>

      <div className="relative">
        <div
          ref={body}
          className="overflow-hidden"
          style={{ maxHeight: unfolded ? undefined : FOLDED_HEIGHT }}
        >
          <MarkdownView body={renderMentions(item.body, people)} />
        </div>

        {/* The veil says the text goes on where the fold falls mid-sentence:
            a message cut clean reads as a message that ended there. */}
        {overflows && !unfolded && (
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-white to-transparent"
          />
        )}
      </div>

      {(overflows || unfolded) && (
        <button
          type="button"
          onClick={() => setUnfolded((was) => !was)}
          className="mt-1 flex cursor-pointer items-center gap-1 text-xs font-medium text-slate-500 transition-colors hover:text-slate-900"
        >
          {unfolded ? (
            <>
              <ChevronUp className="size-3" aria-hidden />
              Replier
            </>
          ) : (
            <>
              <ChevronDown className="size-3" aria-hidden />
              Lire la suite
            </>
          )}
        </button>
      )}
    </article>
  );
}
