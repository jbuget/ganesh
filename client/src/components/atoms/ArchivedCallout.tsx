import { Archive } from "lucide-react";

import { formatDateCourte } from "@/lib/dates";

interface ArchivedCalloutProps {
  /** Quand la mission a quitte le referentiel, si la date est connue. */
  archivedAt: string | null | undefined;
}

/**
 * The state of a mission that no longer appears in the reference list.
 *
 * An archived mission opens like any other, and nothing in the sheet would say
 * it shows up nowhere any more: without this banner, one would edit it
 * believing it a live mission.
 *
 * Missions archived before the date was recorded carry none: the banner then
 * settles for the state, rather than inventing a day.
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
