import type { RoadmapMissionResponse } from "@/lib/api/generated/model";
import { phaseDot } from "@/lib/board";
import { SEGMENT_STYLES, placeOn, positionOf } from "@/lib/roadmap";

interface RoadmapBarProps {
  mission: RoadmapMissionResponse;
  from: string;
  to: string;
}

/**
 * One mission drawn on the axis: what happened, what is supposed, what runs.
 *
 * The three textures are the whole screen. Solid is constaté, hatched is a
 * supposition, a thin rule is a service being kept alive — reading the second
 * as the first is the mistake this drawing exists to prevent, so the
 * difference is carried by the texture and never by the colour alone, which
 * belongs to the phase.
 *
 * The diamond is the date the team announced. When the projection lands past
 * it, a red thread joins the two: the only red on the page, and the one thing
 * the reader should leave with.
 */
export function RoadmapBar({ mission, from, to }: RoadmapBarProps) {
  const target = mission.target_date;
  const targetAt = target ? positionOf(target, from, to) : null;
  const landingAt = mission.landing_date
    ? positionOf(mission.landing_date, from, to)
    : null;

  const slip =
    mission.is_late && targetAt !== null && landingAt !== null
      ? { left: Math.max(0, targetAt), width: Math.max(0, landingAt - targetAt) }
      : null;

  return (
    <div className="relative h-6">
      {mission.segments.map((segment, index) => {
        const placed = placeOn(segment.starts_on, segment.ends_on, from, to);
        if (!placed) return null;

        const style = SEGMENT_STYLES[segment.kind];
        const colour = segment.status ? phaseDot(segment.status) : "bg-slate-300";
        const runs = segment.kind === "running";

        return (
          <span
            key={`${segment.kind}-${segment.starts_on}-${index}`}
            title={`${style.title} · ${segment.starts_on} → ${segment.ends_on}`}
            style={{
              left: `${placed.left * 100}%`,
              width: `${placed.width * 100}%`,
            }}
            className={[
              "absolute top-1/2 -translate-y-1/2",
              // A service that runs is a rule, not a block: it has no length
              // to read, only a direction.
              runs ? "h-0.5" : "h-3",
              colour,
              style.className,
              // A cut end is left square: a rounded one would read as the
              // place the mission starts or stops, which it is not.
              placed.clippedLeft ? "" : "rounded-l-sm",
              placed.clippedRight ? "" : "rounded-r-sm",
            ].join(" ")}
          />
        );
      })}

      {slip && (
        <span
          aria-hidden
          style={{ left: `${slip.left * 100}%`, width: `${slip.width * 100}%` }}
          className="absolute top-1/2 h-px -translate-y-1/2 bg-red-500"
        />
      )}

      {targetAt !== null && targetAt >= 0 && targetAt <= 1 && (
        <span
          title={`Date annoncée : ${target}`}
          style={{ left: `${targetAt * 100}%` }}
          className={[
            "absolute top-1/2 size-2.5 -translate-x-1/2 -translate-y-1/2 rotate-45 border",
            mission.is_late ? "border-red-600 bg-red-500" : "border-slate-600 bg-white",
          ].join(" ")}
        />
      )}
    </div>
  );
}
