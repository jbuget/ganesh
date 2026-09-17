import type { BoardMemberResponse } from "@/lib/api/generated/model";

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
 */
export function MemberAvatars({ membres }: MemberAvatarsProps) {
  if (membres.length === 0) return null;

  const affiches = membres.slice(0, VISIBLES);
  const restants = membres.length - affiches.length;

  return (
    <div className="flex items-center -space-x-1.5">
      {affiches.map((membre) => (
        <span
          key={membre.id}
          title={membre.display_name}
          className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-200 text-[10px] font-medium text-slate-700"
        >
          {membre.initiales}
        </span>
      ))}

      {restants > 0 && (
        <span
          title={membres
            .slice(VISIBLES)
            .map((m) => m.display_name)
            .join(", ")}
          className="flex size-6 items-center justify-center rounded-full border border-white bg-slate-100 text-[10px] font-medium text-slate-500"
        >
          +{restants}
        </span>
      )}
    </div>
  );
}
