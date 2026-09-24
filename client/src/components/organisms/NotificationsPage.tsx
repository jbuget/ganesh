"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { PageHeader } from "@/components/atoms/PageHeader";
import { RunRemindersPanel } from "@/components/atoms/RunRemindersPanel";
import { NotificationItem } from "@/components/molecules/NotificationItem";
import { PageLayout } from "@/components/organisms/PageLayout";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { Button } from "@/components/ui/button";
import type { NotificationFilter } from "@/lib/api/generated/model";
import { useOpenedMission } from "@/lib/opened-mission";
import { STRONG_RULE } from "@/lib/table-frame";
import { useCurrentUser } from "@/lib/api/queries";
import { useInbox } from "@/lib/use-inbox";
import { holds } from "@/lib/roles";

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
 *
 * A line about an update opens the project beside the list rather than
 * carrying the reader off to its page: one comes to go through what one was
 * told, and closing the panel puts the reader back where they were, on the
 * next line down.
 *
 * At the foot, and for managers alone, the one gesture that writes to the
 * whole team: sending a round of reminder letters by hand. It is the odd one
 * out on a page that is otherwise entirely one's own, and it is kept apart by
 * a rule rather than moved — every other home for it would be worse.
 */
export function NotificationsPage() {
  const inbox = useInbox();
  const { user } = useCurrentUser();
  const panel = useOpenedMission();
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

        {panel.openedMission && (
          <ProjectPanel
            key={`${panel.openedMission}:${panel.openTab ?? ""}:${panel.aimedAt ?? ""}`}
            projectId={panel.openedMission}
            tab={panel.openTab}
            aimedAt={panel.aimedAt}
            onClose={panel.close}
            // Nothing on this screen reads the mission: the inbox says what
            // one was told, and a phase changed in the panel changes none of
            // those sentences.
            onMissionChanged={() => {}}
            onOpenMission={(projectId) => panel.open(projectId)}
          />
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

        {holds(user?.role, "MANAGER") && <RunRemindersPanel />}
      </div>
    </PageLayout>
  );
}
