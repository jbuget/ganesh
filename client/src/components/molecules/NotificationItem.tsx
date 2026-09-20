"use client";

import { Check, Undo2 } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import type { NotificationResponse } from "@/lib/api/generated/model";
import { notificationSentence } from "@/lib/notifications";
import { since } from "@/lib/relative-dates";

interface NotificationItemProps {
  notification: NotificationResponse;
  /** Passed in rather than read here, so the wording is under test. */
  now: Date;
  onToggleRead: (id: number, read: boolean) => void;
}

/**
 * One line of the inbox: a sentence, when, and the way to settle it.
 *
 * A sentence and not a row of columns — what one was told is read, not
 * scanned, and a table of « type / sujet / date » would ask the reader to
 * recompose the sentence themselves.
 *
 * A line waiting to be seen carries a dot and a slightly stronger ground: the
 * two together survive both a colour-blind reader and a grey-on-grey screen.
 */
export function NotificationItem({
  notification,
  now,
  onToggleRead,
}: NotificationItemProps) {
  const said = notificationSentence(notification);
  const isRead = notification.read_at !== null;

  const subject: ReactNode = said.about ? (
    <span className="font-medium text-slate-900">{said.about}</span>
  ) : null;

  const sentence = (
    <span className="min-w-0">
      <span className="font-medium text-slate-900">{said.who}</span>{" "}
      <span className="text-slate-600">{said.what}</span> {subject}
    </span>
  );

  return (
    <li
      className={[
        "flex items-start gap-3 border-b border-slate-200 px-4 py-3 text-sm transition-colors last:border-b-0",
        isRead ? "bg-white" : "bg-slate-50",
      ].join(" ")}
    >
      {isRead ? (
        <span aria-hidden className="mt-1.5 size-2 shrink-0" />
      ) : (
        <span
          aria-hidden
          data-testid="unread-mark"
          className="mt-1.5 size-2 shrink-0 rounded-full bg-blue-500"
        />
      )}

      <span className="min-w-0 flex-1">
        {said.href ? (
          <Link
            href={said.href}
            className="block cursor-pointer rounded hover:underline"
          >
            {sentence}
          </Link>
        ) : (
          sentence
        )}

        <span className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
          <span>{since(notification.at, now)}</span>
          {said.detail && (
            <>
              <span aria-hidden className="text-slate-300">
                ·
              </span>
              <span>{said.detail}</span>
            </>
          )}
        </span>
      </span>

      <button
        type="button"
        aria-label={isRead ? "Marquer comme non lu" : "Marquer comme lu"}
        title={isRead ? "Marquer comme non lu" : "Marquer comme lu"}
        onClick={() => onToggleRead(notification.id, !isRead)}
        className="shrink-0 cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
      >
        {isRead ? (
          <Undo2 className="size-4" aria-hidden />
        ) : (
          <Check className="size-4" aria-hidden />
        )}
      </button>
    </li>
  );
}
