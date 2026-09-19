import { MOODS } from "@/lib/mood";

/**
 * What the five shades mean, once they are read as surfaces.
 *
 * The record names every level beside its face; the chart fills them, and a
 * filled shade with nothing to name it is a colour one has to guess. Read in
 * the order of the scale, so the legend climbs as the bars do.
 */
export function MoodLegend() {
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1">
      {MOODS.map((level) => {
        const Icon = level.icon;

        return (
          <li key={level.value} className="flex items-center gap-1.5 text-xs">
            <Icon className={`size-4 shrink-0 ${level.colour}`} aria-hidden />
            <span className="text-slate-600">{level.label}</span>
          </li>
        );
      })}
    </ul>
  );
}
