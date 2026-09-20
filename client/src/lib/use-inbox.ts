"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { NotificationFilter } from "@/lib/api/generated/model";
import {
  getListNotificationsQueryKey,
  useSetNotificationsReadState,
} from "@/lib/api/generated/notifications/notifications";
import { useNotifications } from "@/lib/api/queries";

/** How many lines a page of the inbox holds. */
export const PAGE_SIZE = 20;

/** Every page of the inbox, whatever its filter or its offset. */
const EVERY_PAGE = getListNotificationsQueryKey().slice(0, 1);

/**
 * State and actions of the inbox: the panel's and the page's alike.
 *
 * Both read the same route and write through the same mutation, so the bell
 * settles the moment a line is marked from either one. The screens carry the
 * rendering and nothing else.
 */
export function useInbox({
  status = "all",
  pageSize = PAGE_SIZE,
  poll = true,
}: {
  status?: NotificationFilter;
  pageSize?: number;
  poll?: boolean;
} = {}) {
  const [filter, setFilter] = useState<NotificationFilter>(status);
  const [page, setPage] = useState(0);

  const queryClient = useQueryClient();
  const feed = useNotifications(
    { status: filter, limit: pageSize, offset: page * pageSize },
    { poll },
  );
  const settle = useSetNotificationsReadState();

  async function write(ids: number[] | null, read: boolean) {
    await settle.mutateAsync({ data: { ids, read } });
    // Every page at once: marking a line seen changes the bell, the panel and
    // whichever page of the list is open behind it.
    await queryClient.invalidateQueries({ queryKey: EVERY_PAGE });
  }

  return {
    ...feed,
    filter,
    page,
    pageSize,
    /** Whether asking for the next page would bring anything back. */
    hasMore: (page + 1) * pageSize < feed.total,
    isSettling: settle.isPending,

    show(next: NotificationFilter) {
      setFilter(next);
      // The offset belongs to the list one was reading: kept across a change
      // of filter, page three of « toutes » lands on an empty page four of
      // « non lues ».
      setPage(0);
    },
    goToPage(next: number) {
      setPage(Math.max(0, next));
    },

    toggleRead(id: number, read: boolean) {
      return write([id], read);
    },
    markAllRead() {
      return write(null, true);
    },
  };
}
