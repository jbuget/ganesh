import type { MoodLevel } from "@/lib/api/generated/model";
import { mood } from "@/lib/mood";

interface MoodMarkProps {
  level: MoodLevel;
  /** Who posted it. The screen names everyone, and says so. */
  initials: string;
}

/**
 * One posted mood: a coloured face, initials in ordinary text.
 *
 * The face carries the level by the shape of its mouth as much as by its
 * shade, so a row reads without telling the colours apart. The initials are
 * what make the screen nominative; the full name comes on hover, from the row,
 * because initials cannot be guessed.
 */
export function MoodMark({ level, initials }: MoodMarkProps) {
  const face = mood(level);
  if (!face) return null;

  const Icon = face.icon;

  return (
    <span className="flex items-center gap-1 text-slate-600">
      <Icon className={`size-5 shrink-0 ${face.colour}`} aria-hidden />
      <span className="text-xs font-medium tabular-nums">{initials}</span>
    </span>
  );
}
