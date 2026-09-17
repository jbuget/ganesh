"use client";

import type { BoardMemberResponse } from "@/lib/api/generated/model";
import { useTooltipCurseur } from "@/lib/use-tooltip-curseur";

/** Au-dela, les pastilles se chevauchent trop pour rester lisibles. */
const VISIBLES = 4;

interface MemberAvatarsProps {
  membres: BoardMemberResponse[];
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
export function MemberAvatars({ membres }: MemberAvatarsProps) {
  const { tooltip, suivre, quitter } = useTooltipCurseur();

  if (membres.length === 0) return null;

  const affiches = membres.slice(0, VISIBLES);
  const restants = membres.slice(VISIBLES);

  return (
    <div className="flex items-center -space-x-1.5" onMouseLeave={quitter}>
      {affiches.map((membre) => (
        <span
          key={membre.id}
          onMouseMove={(event) => suivre(event, membre.display_name)}
          className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-200 text-[10px] font-medium text-slate-700"
        >
          {membre.initiales}
        </span>
      ))}

      {restants.length > 0 && (
        <span
          onMouseMove={(event) =>
            suivre(event, restants.map((m) => m.display_name).join(", "))
          }
          className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-100 text-[10px] font-medium text-slate-500"
        >
          +{restants.length}
        </span>
      )}

      {tooltip}
    </div>
  );
}
