import Link from "next/link";

import { PresenceMark } from "@/components/atoms/PresenceMark";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import type { UserResponse } from "@/lib/api/generated/model";
import { dayShown, presenceOfDay } from "@/lib/presence";
import { STRONG_RULE } from "@/lib/table-frame";

/** Beyond this, the avatars stop being faces and become a wall. */
const NAMED = 8;

const LINK = "cursor-pointer underline-offset-2 hover:text-slate-900 hover:underline";

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
}: {
  /** The active team. A teammate who said nothing counts as on site. */
  users: UserResponse[];
  today: Date;
  /** Who is reading, so the block can hand them their own week to change. */
  meId?: number | null;
}) {
  if (users.length === 0) return null;

  const day = dayShown(today);
  const counted = presenceOfDay(
    users.map((user) => user.presence),
    day.key,
  );
  const onSite = users.filter(
    (user) => (user.presence?.[day.key] ?? "ON_SITE") === "ON_SITE",
  );

  return (
    <section className={`rounded-xl border bg-white p-3 ${STRONG_RULE}`}>
      <header className="mb-2 flex items-baseline justify-between gap-2">
        <h2 className="text-sm font-medium text-slate-700">
          {day.isToday ? "Aujourd'hui" : day.label}
        </h2>
        {/* Two ways out, and only these two: one to change one's own week,
            one to read everyone's. The block itself still declares nothing. */}
        <nav className="flex items-center gap-2 text-xs text-slate-500">
          {meId !== null && (
            <>
              <Link href={`/users?user=${meId}`} className={LINK}>
                Ma présence
              </Link>
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
        <span className="flex items-center gap-1.5">
          <PresenceMark day="ON_SITE" labelled={false} />
          <span className="tabular-nums">{counted.onSite}</span> sur site
        </span>
        <span className="flex items-center gap-1.5">
          <PresenceMark day="REMOTE" labelled={false} />
          <span className="tabular-nums">{counted.remote}</span> en télétravail
        </span>
        {counted.away > 0 && (
          <span className="text-slate-500">
            <span className="tabular-nums">{counted.away}</span> absent
            {counted.away > 1 ? "s" : ""}
          </span>
        )}
      </p>

      {/* The faces of those in, because a figure says how many and a face says
          who — which is what one actually came to find out. */}
      {onSite.length > 0 && (
        <ul className="mt-2.5 flex flex-wrap gap-1">
          {onSite.slice(0, NAMED).map((user) => (
            <li key={user.id}>
              <UserAvatar initials={user.initials} name={user.display_name} />
              {/* The avatar carries a `title`, which a screen reader may not
                  announce — and here the faces are the whole answer. */}
              <span className="sr-only">{user.display_name}</span>
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
