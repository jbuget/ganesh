import { Newspaper } from "lucide-react";
import Link from "next/link";

import type { DigestResponse } from "@/lib/api/generated/model";
import { formatMonth, type MonthCursor } from "@/lib/dates";
import { gazetteTeaser } from "@/lib/gazette";

interface GazetteBandProps {
  cursor: MonthCursor;
  digest: DigestResponse;
}

/**
 * La Gazette, read from the home screen.
 *
 * A band rather than a tab of the bar: a page written once a month asked for a
 * rank beside screens one opens hourly, and it never earned it. Here it sits
 * just above « Quoi de neuf », and the two read as one movement — the month of
 * the whole company, then the news of my own projects.
 *
 * It reads and hands over, and that is the whole rule. Generating is a write:
 * it is traced, it keeps the version beside the last, and it belongs on the
 * screen that carries the picker those versions are opened from. A button here
 * would let somebody write a digest without ever seeing the one before it.
 *
 * The month is the running one, the same a bare `/gazette` opens on: the link
 * therefore carries no address of its own, and what one clicks through to is
 * what the band was showing.
 */
export function GazetteBand({ cursor, digest }: GazetteBandProps) {
  return (
    <Link
      href="/gazette"
      className="block cursor-pointer rounded-xl border border-slate-300 bg-white px-3 py-2.5 transition-colors hover:border-slate-400 hover:bg-slate-50"
    >
      <span className="flex items-center gap-1.5">
        <Newspaper className="size-3.5 shrink-0 text-slate-400" aria-hidden />
        <span className="text-sm font-medium text-slate-700">La Gazette</span>
        <span className="ml-auto text-xs text-slate-400">
          {formatMonth(cursor.year, cursor.month)}
        </span>
      </span>

      {/* Clamped rather than cut in the code: the chapeau is two or three
          sentences, and where it stops is a matter of the width it is read at,
          not of a length decided here. */}
      <span className="mt-1 line-clamp-3 block text-xs text-slate-500">
        {gazetteTeaser(digest)}
      </span>
    </Link>
  );
}
