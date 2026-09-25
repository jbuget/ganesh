"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { PresenceMark } from "@/components/atoms/PresenceMark";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import type { UserResponse } from "@/lib/api/generated/model";
import { dayShown, peopleOfDay } from "@/lib/presence";
import { STRONG_RULE } from "@/lib/table-frame";
import { useCursorTooltip } from "@/lib/use-cursor-tooltip";

/** Beyond this, the avatars stop being faces and become a wall. */
const NAMED = 8;

const LINK = "cursor-pointer underline-offset-2 hover:text-slate-900 hover:underline";

/**
 * A figure that says who, when asked.
 *
 * Three lists printed side by side would bury the faces below, and the faces
 * are what one came for. The names therefore wait under the cursor — without
 * the second of hesitation the native `title` costs, which is a second too
 * long while running along three figures — and are said outright to whoever
 * reads with their ears: « 1 en télétravail » otherwise leaves one wondering
 * which one, and a bubble is nothing to an ear.
 *
 * A place nobody is in offers nothing: an empty bubble is worse than none.
 */
function Place({
  people,
  className = "",
  children,
}: {
  people: UserResponse[];
  className?: string;
  children: ReactNode;
}) {
  // The bubble belongs to the figure that opens it: it is mounted on hover and
  // nowhere before, so three of them cost no more than one shared between them.
  const { tooltip, follow, leave } = useCursorTooltip();

  const figure = `flex items-center gap-1.5 ${className}`;
  if (people.length === 0) return <span className={figure}>{children}</span>;

  const names = people.map((one) => one.display_name).join(", ");

  return (
    <span
      onMouseMove={(event) =>
        // The bubble is one line by default, and a full office would run off
        // the screen: a list of names is allowed to wrap.
        follow(event, <span className="block max-w-xs whitespace-normal">{names}</span>)
      }
      onMouseLeave={leave}
      className={`cursor-help ${figure}`}
    >
      {children}
      {/* Read out after the figure it belongs to, which names the place: the
          ear hears « 1 en télétravail Malik » in one go. */}
      <span className="sr-only">{names}</span>
      {tooltip}
    </span>
  );
}

/**
 * Who is in today, and from where.
 *
 * Read, never written: declaring one's own week happens once and then almost
 * never, and a picker posted here would be noise every morning for a gesture
 * made twice a year. Who is around, on the other hand, is worth knowing each
 * day — whether to walk over or to call, whether the room will be full.
 *
 * It hands over rather than acting, like everything else on this screen: the
 * whole week is one click away, on the tab that holds it.
 */
export function TodayPresence({
  users,
  today,
  meId = null,
  onOpenMine,
}: {
  /** The active team. A teammate who said nothing counts as on site. */
  users: UserResponse[];
  today: Date;
  /** Who is reading, so the block can hand them their own week to change. */
  meId?: number | null;
  /** Opens a teammate's panel where the reader stands, without leaving. */
  onOpenMine?: () => void;
}) {
  if (users.length === 0) return null;

  const day = dayShown(today);
  const { onSite, remote, away } = peopleOfDay(users, day.key);
  const manyAway = away.length > 1 ? "s" : "";

  return (
    <section className={`rounded-xl border bg-white p-3 ${STRONG_RULE}`}>
      <header className="mb-2 flex items-baseline justify-between gap-2">
        <h2 className="text-sm font-medium text-slate-700">
          {day.isToday ? "Aujourd'hui" : day.label}
        </h2>
        {/* Two ways out, and only these two. One's own week opens where the
            reader stands — changing a day is not worth a screen — while the
            whole team's is another screen, and reached as one. */}
        <nav className="flex items-center gap-2 text-xs text-slate-500">
          {meId !== null && onOpenMine && (
            <>
              <button type="button" onClick={onOpenMine} className={LINK}>
                Ma présence
              </button>
              <span aria-hidden className="text-slate-300">
                |
              </span>
            </>
          )}
          <Link href="/users?vue=presence" className={LINK}>
            Toute la semaine
          </Link>
        </nav>
      </header>

      <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-700">
        <Place people={onSite}>
          <PresenceMark day="ON_SITE" labelled={false} />
          <span className="tabular-nums">{onSite.length}</span> sur site
        </Place>
        <Place people={remote}>
          <PresenceMark day="REMOTE" labelled={false} />
          <span className="tabular-nums">{remote.length}</span> en télétravail
        </Place>
        {away.length > 0 && (
          <Place people={away} className="text-slate-500">
            <span className="tabular-nums">{away.length}</span> absent
            {manyAway}
          </Place>
        )}
      </p>

      {/* The faces of those in, because a figure says how many and a face says
          who — which is what one actually came to find out. */}
      {onSite.length > 0 && (
        // Hidden from a screen reader: the figure above already names them, and
        // names them all, where the faces stop at eight.
        <ul aria-hidden className="mt-2.5 flex flex-wrap gap-1">
          {onSite.slice(0, NAMED).map((user) => (
            <li key={user.id}>
              <UserAvatar initials={user.initials} name={user.display_name} />
            </li>
          ))}
          {onSite.length > NAMED && (
            <li className="self-center text-xs text-slate-500">
              +{onSite.length - NAMED}
            </li>
          )}
        </ul>
      )}
    </section>
  );
}
