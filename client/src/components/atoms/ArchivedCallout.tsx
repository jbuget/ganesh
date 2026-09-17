import { Archive } from "lucide-react";

import { formatDateCourte } from "@/lib/dates";

interface ArchivedCalloutProps {
  /** Quand la mission a quitte le referentiel, si la date est connue. */
  archivedAt: string | null | undefined;
}

/**
 * L'etat d'une mission qui ne figure plus au referentiel.
 *
 * Une mission archivee s'ouvre comme les autres, et rien dans la fiche ne
 * dirait qu'elle n'apparait plus nulle part : sans ce bandeau, on la
 * modifierait en croyant travailler sur une mission vivante.
 *
 * Les missions archivees avant que la date ne soit enregistree n'en portent
 * pas : le bandeau se contente alors de l'etat, plutot que d'inventer un jour.
 */
export function ArchivedCallout({ archivedAt }: ArchivedCalloutProps) {
  return (
    <p
      role="status"
      className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900"
    >
      <Archive className="size-4 shrink-0 text-amber-600" aria-hidden />
      {archivedAt
        ? `Cette mission a été archivée le ${formatDateCourte(archivedAt)}.`
        : "Cette mission est archivée."}
    </p>
  );
}
