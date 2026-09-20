"use client";

import { Bell } from "lucide-react";
import { forwardRef, type ComponentPropsWithoutRef } from "react";

interface NotificationBellProps extends ComponentPropsWithoutRef<"button"> {
  /** How many lines are still waiting to be seen. */
  unreadCount: number;
  /** Folded, the bar leaves room for the bell alone. */
  collapsed?: boolean;
}

/** Past this, the badge says « beaucoup » rather than a figure nobody reads. */
const TOO_MANY = 99;

/**
 * The bell at the foot of the bar, and what is waiting behind it.
 *
 * Unfolded it reads as a line — icon, name, count — like the screens above it
 * and the account below: an icon alone on a full-width band reads as something
 * left there rather than as something to click. Folded it becomes the icon and
 * a bare dot, since there is no room for a figure and unfolding the bar is all
 * it takes to know how many.
 *
 * The exact count is said out loud in both, where a screen reader has all the
 * room it needs.
 *
 * It forwards whatever it is handed — a popover opens by grafting its own
 * handlers onto the element that triggers it, and a trigger wrapped in a
 * second button would nest one inside the other.
 */
export const NotificationBell = forwardRef<HTMLButtonElement, NotificationBellProps>(
  function NotificationBell({ unreadCount, collapsed = false, ...rest }, ref) {
    const waiting = unreadCount > 0;
    const label = waiting
      ? `Notifications, ${unreadCount} non lue${unreadCount > 1 ? "s" : ""}`
      : "Notifications";
    const shown = unreadCount > TOO_MANY ? `${TOO_MANY}+` : unreadCount;

    return (
      <button
        ref={ref}
        type="button"
        aria-label={label}
        title={collapsed ? label : undefined}
        {...rest}
        className={[
          "flex w-full cursor-pointer items-center gap-2.5 rounded-md py-2 text-sm transition-colors",
          collapsed ? "relative justify-center px-0" : "px-3",
          waiting
            ? "font-medium text-slate-900 hover:bg-slate-100"
            : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
        ].join(" ")}
      >
        <Bell className="size-4 shrink-0" aria-hidden />

        {collapsed ? (
          waiting && (
            <span
              aria-hidden
              className="absolute right-2.5 top-1.5 size-2 rounded-full bg-red-500 ring-2 ring-white"
            />
          )
        ) : (
          <>
            <span aria-hidden className="min-w-0 flex-1 text-left">
              Notifications
            </span>
            {waiting && (
              <span
                aria-hidden
                className="flex min-w-5 shrink-0 items-center justify-center rounded-full bg-red-500 px-1.5 text-[11px] font-medium leading-5 text-white tabular-nums"
              >
                {shown}
              </span>
            )}
          </>
        )}
      </button>
    );
  },
);
