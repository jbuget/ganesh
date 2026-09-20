"use client";

import Link from "next/link";
import { useState } from "react";

import { NotificationBell } from "@/components/atoms/NotificationBell";
import { NotificationItem } from "@/components/molecules/NotificationItem";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useInbox } from "@/lib/use-inbox";

/** How many lines the panel holds before sending one to the page. */
const GLANCE = 10;

/**
 * The bell in the sidebar, and what is waiting behind it.
 *
 * A lucarne, not the inbox: the last few lines, and the way to the page that
 * holds the rest. Which is why it asks for what is waiting rather than for
 * everything — the panel answers « quoi de neuf », the page answers « qu'est-ce
 * qu'on m'a dit ».
 */
export function NotificationPanel({ collapsed = false }: { collapsed?: boolean }) {
  const [isOpen, setOpen] = useState(false);
  const inbox = useInbox({ status: "unread", pageSize: GLANCE });
  const now = new Date();

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        render={
          <NotificationBell unreadCount={inbox.unreadCount} collapsed={collapsed} />
        }
      />

      <PopoverContent align="start" side="top" className="w-96 gap-0 p-0">
        <div className="flex items-center justify-between gap-2 border-b border-slate-200 px-4 py-2.5">
          <p className="text-sm font-semibold">Notifications</p>
          {inbox.unreadCount > 0 && (
            <button
              type="button"
              onClick={() => void inbox.markAllRead()}
              disabled={inbox.isSettling}
              className="cursor-pointer rounded px-1.5 py-0.5 text-xs text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Tout marquer comme lu
            </button>
          )}
        </div>

        {inbox.entries.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-slate-500">
            Rien de nouveau.
          </p>
        ) : (
          <ul className="max-h-96 overflow-y-auto">
            {inbox.entries.map((entry) => (
              <NotificationItem
                key={entry.id}
                notification={entry}
                now={now}
                onToggleRead={(id, read) => void inbox.toggleRead(id, read)}
              />
            ))}
          </ul>
        )}

        <div className="border-t border-slate-200 p-1">
          <Link
            href="/notifications"
            onClick={() => setOpen(false)}
            className="block cursor-pointer rounded px-2 py-1.5 text-center text-sm text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            Tout voir
          </Link>
        </div>
      </PopoverContent>
    </Popover>
  );
}
