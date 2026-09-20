"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { PageHeader } from "@/components/atoms/PageHeader";
import { NotificationItem } from "@/components/molecules/NotificationItem";
import { PageLayout } from "@/components/organisms/PageLayout";
import { Button } from "@/components/ui/button";
import type { NotificationFilter } from "@/lib/api/generated/model";
import { STRONG_RULE } from "@/lib/table-frame";
import { useInbox } from "@/lib/use-inbox";

const FILTERS: { value: NotificationFilter; label: string }[] = [
  { value: "all", label: "Toutes" },
  { value: "unread", label: "Non lues" },
];

/**
 * Everything one has been told, page by page.
 *
 * The panel in the sidebar is a lucarne; this is the inbox. What it adds is
 * what a popover cannot hold: the history, the filter, and somewhere to come
 * back to a line one had left waiting.
 *
 * A list of sentences rather than a table: a notification is read, not
 * scanned, and columns would ask the reader to recompose the sentence
 * themselves.
 */
export function NotificationsPage() {
  const inbox = useInbox();
  const now = new Date();
  const first = inbox.page * inbox.pageSize;

  const header = (
    <PageHeader
      title="Notifications"
      subtitle="Ce qui vous concerne : vos projets, vos mois, votre compte."
      actions={
        inbox.unreadCount > 0 && (
          <Button
            variant="outline"
            className="cursor-pointer"
            disabled={inbox.isSettling}
            onClick={() => void inbox.markAllRead()}
          >
            Tout marquer comme lu
          </Button>
        )
      }
    />
  );

  return (
    <PageLayout header={header}>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          {FILTERS.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              aria-pressed={inbox.filter === value}
              onClick={() => inbox.show(value)}
              className={[
                "cursor-pointer rounded-md px-3 py-1.5 text-sm transition-colors",
                inbox.filter === value
                  ? "bg-slate-100 font-medium text-slate-900"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
              ].join(" ")}
            >
              {/* The figure sits on the filter it narrows to, and stays whole
                  whichever list is being read. */}
              {value === "unread" && inbox.unreadCount > 0
                ? `${label} (${inbox.unreadCount})`
                : label}
            </button>
          ))}
        </div>

        {inbox.isLoading ? (
          <p className="text-sm text-slate-500">Chargement…</p>
        ) : inbox.entries.length === 0 ? (
          <p className="border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
            {inbox.filter === "unread" ? "Rien en attente." : "Aucune notification."}
          </p>
        ) : (
          // The frame is the one every list of the application is drawn in:
          // strong rule, square corners. A frame a shade lighter, or rounded,
          // would read as a card laid on the page rather than as one more
          // list in it.
          <ul className={`border ${STRONG_RULE}`}>
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

        {(inbox.page > 0 || inbox.hasMore) && (
          <div className="flex items-center justify-between gap-4">
            <p className="text-sm text-slate-500 tabular-nums">
              {first + 1}–{Math.min(first + inbox.pageSize, inbox.total)} sur{" "}
              {inbox.total}
            </p>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                aria-label="Page précédente"
                className="cursor-pointer"
                disabled={inbox.page === 0}
                onClick={() => inbox.goToPage(inbox.page - 1)}
              >
                <ChevronLeft />
              </Button>
              <Button
                variant="outline"
                size="icon"
                aria-label="Page suivante"
                className="cursor-pointer"
                disabled={!inbox.hasMore}
                onClick={() => inbox.goToPage(inbox.page + 1)}
              >
                <ChevronRight />
              </Button>
            </div>
          </div>
        )}
      </div>
    </PageLayout>
  );
}
