import type { ProjectResponse } from "@/lib/api/generated/model";
import { Badge } from "@/components/ui/badge";

interface MondayLinkProps {
  project: ProjectResponse;
}

/**
 * Etat du rattachement d'une mission a Monday.
 *
 * Tant qu'une mission n'est pas rattachee, elle ne remontera pas dans Monday :
 * l'information doit se lire sans avoir a la chercher.
 */
export function MondayLink({ project }: MondayLinkProps) {
  if (project.kind === "hors_projet") {
    return <span className="text-xs text-slate-400">—</span>;
  }

  return project.is_syncable_to_monday ? (
    <Badge variant="secondary">Rattaché</Badge>
  ) : (
    <Badge variant="outline" className="text-slate-500">
      Non rattaché
    </Badge>
  );
}
