"use client";

import type { BoardMemberResponse } from "@/lib/api/generated/model";
import { useCursorTooltip } from "@/lib/use-cursor-tooltip";

/** Past this, the avatars overlap too much to stay readable. */
const VISIBLES = 4;

interface MemberAvatarsProps {
  members: BoardMemberResponse[];
}

/**
 * A mission's contributors, as initial avatars.
 *
 * These are the people who declared time on it, forecasts included: knowing who
 * is about to start counts as much as knowing who has worked on it.
 *
 * Initials cannot be guessed: the tooltip gives the name without delay, where
 * the native `title` attribute leaves one hesitating for a second.
 */
export function MemberAvatars({ members }: MemberAvatarsProps) {
  const { tooltip, follow, leave } = useCursorTooltip();

  if (members.length === 0) return null;

  const shown = members.slice(0, VISIBLES);
  const remaining = members.slice(VISIBLES);

  return (
    <div className="flex items-center -space-x-1.5" onMouseLeave={leave}>
      {shown.map((member) => (
        <span
          key={member.id}
          onMouseMove={(event) => follow(event, member.display_name)}
          className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-200 text-[10px] font-medium text-slate-700"
        >
          {member.initials}
        </span>
      ))}

      {remaining.length > 0 && (
        <span
          onMouseMove={(event) =>
            follow(event, remaining.map((m) => m.display_name).join(", "))
          }
          className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-100 text-[10px] font-medium text-slate-500"
        >
          +{remaining.length}
        </span>
      )}

      {tooltip}
    </div>
  );
}
