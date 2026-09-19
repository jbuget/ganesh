import { Globe } from "lucide-react";

interface PublishedMarkProps {
  /** Whether the catalogue picks the mission up. */
  published: boolean;
}

/**
 * Whether the mission has a card on waat.tools.
 *
 * Only what is published is drawn: an empty cell says the mission has no
 * service sheet yet, which is what one scans the column for. Saying « non
 * publié » on fifty rows would bury the dozen that are.
 *
 * A globe rather than a dot: the phase already carries a round mark on the
 * same line, and two marks of one shape read as the same information. The
 * glyph also says which catalogue — a public address, not a state of the
 * mission.
 */
export function PublishedMark({ published }: PublishedMarkProps) {
  if (!published) return null;

  return (
    <span className="flex items-center gap-1.5 text-slate-700">
      <Globe className="size-3.5 shrink-0 text-emerald-600" aria-hidden />
      Publié
    </span>
  );
}
