"use client";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import type { HomeUpdate } from "@/lib/home";
import { since } from "@/lib/relative-dates";

interface UpdateFeedItemProps {
  entry: HomeUpdate;
  /** Freezes the reference time: without it, server and client would diverge. */
  now: Date;
  /** Opens the mission on its thread — which is where the message lives. */
  onOpen: (projectId: number) => void;
}

/**
 * One piece of news from a mission one works on.
 *
 * The mission names the entry, the author and the moment sign it: the feed
 * mixes several threads, and a message read without knowing which mission it
 * speaks of says nothing.
 *
 * Long messages are cut rather than shown whole: the feed announces, the
 * thread reads. Cut by clamping the lines rather than by laying a fade over
 * the box — a fade tall enough to be seen also greys out the one-line messages,
 * which are most of them.
 */
export function UpdateFeedItem({ entry, now, onOpen }: UpdateFeedItemProps) {
  const { item, update } = entry;

  return (
    <article
      // The card as a whole opens the thread; the controls it carries keep
      // their own click, or the name would fire the handler twice.
      onClick={(event) => {
        if ((event.target as HTMLElement).closest("button")) return;
        onOpen(item.project.id);
      }}
      className="cursor-pointer rounded-lg border border-slate-300 bg-white p-3 shadow-xs transition-shadow hover:border-slate-500 hover:shadow-sm"
    >
      <header className="flex items-center gap-2">
        <UserAvatar
          initials={update.author.initials}
          name={update.author.display_name}
        />
        <span className="min-w-0 flex-1">
          {/*
            The whole card opens the thread, but the project name carries the
            same action as a button: a card whose only handler sits on the
            article is reachable by the mouse alone, and this feed is read as
            much with the keyboard as the rest of the screen.
          */}
          <button
            type="button"
            onClick={() => onOpen(item.project.id)}
            className="block max-w-full cursor-pointer truncate text-left text-sm font-medium text-slate-900 hover:underline"
          >
            {item.project.label}
          </button>
          <span className="block truncate text-xs text-slate-500">
            {update.author.display_name} · {since(update.published_at, now)}
          </span>
        </span>
      </header>

      {/* The clamp bites on the paragraphs, where the words are; the height cap
          catches what markdown puts elsewhere — a list, a table, a quote. */}
      <div className="mt-2 max-h-28 overflow-hidden text-sm [&_p]:line-clamp-3">
        <MarkdownView body={update.body} />
      </div>
    </article>
  );
}
