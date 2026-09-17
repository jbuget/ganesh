"use client";

import type { BoardMemberResponse } from "@/lib/api/generated/model";
import { useCursorTooltip } from "@/lib/use-tooltip-curseur";

/** Au-dela, les pastilles se chevauchent trop pour rester lisibles. */
const VISIBLES = 4;

interface MemberAvatarsProps {
  members: BoardMemberResponse[];
}

/**
 * Intervenants d'une mission, en pastilles d'initiales.
 *
 * Ce sont les personnes ayant declare du temps dessus, previsionnel compris :
 * savoir qui s'y mettra compte autant que savoir qui y a travaille.
 *
 * Des initiales ne se devinent pas : l'infobulle donne le nom sans attendre,
 * la ou l'attribut `title` natif laisse hesiter une seconde.
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
