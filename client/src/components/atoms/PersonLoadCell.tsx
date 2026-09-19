import { formatDecimalDays } from "@/lib/dates";

interface PersonLoadCellProps {
  /** Working days the week holds, holidays already taken out. */
  capacity: number;
  /** What is already declared on it: delivered, forecast and leave alike. */
  booked: number;
  /** What the projection placed on top. A hypothesis, not a fact. */
  projected: number;
  /** The half day a week nobody may plan on. */
  reserved: number;
  isOverloaded: boolean;
}

/**
 * One week of one person's diary.
 *
 * Three bands, never merged: what is declared is solid, what the projection
 * added is hatched, and the half day held back each week is left pale at the
 * end. The distinctions are the whole reading — a fact, a hypothesis, and time
 * nobody may plan on — and steering must never take one for another.
 *
 * A week with no working day at all — the one Christmas falls in — shows
 * struck through rather than empty: nobody is free that week, they are absent.
 */
export function PersonLoadCell({
  capacity,
  booked,
  projected,
  reserved,
  isOverloaded,
}: PersonLoadCellProps) {
  if (capacity <= 0) {
    return (
      <div className="flex h-6 items-center justify-center text-[11px] text-slate-300">
        —
      </div>
    );
  }

  const taken = booked + projected;
  const bookedPart = Math.min(100, (booked / capacity) * 100);
  const projectedPart = Math.min(100 - bookedPart, (projected / capacity) * 100);
  const reservedPart = Math.min(
    100 - bookedPart - projectedPart,
    (reserved / capacity) * 100,
  );

  return (
    <div
      className="flex h-6 flex-col justify-center gap-0.5"
      title={`${formatDecimalDays(booked)} j déclarés, ${formatDecimalDays(projected)} j projetés, ${formatDecimalDays(reserved)} j réservés sur ${formatDecimalDays(capacity)} j`}
    >
      <span
        className={[
          "text-center text-[11px] tabular-nums",
          isOverloaded ? "font-semibold text-red-600" : "text-slate-600",
        ].join(" ")}
      >
        {taken > 0 ? formatDecimalDays(Math.round(taken * 10) / 10) : ""}
      </span>

      <div className="flex h-1 w-full overflow-hidden rounded-full bg-slate-200">
        <span
          className={isOverloaded ? "bg-red-500" : "bg-slate-500"}
          style={{ width: `${bookedPart}%` }}
        />
        {/* Hatched: what a projection placed is not what someone declared. */}
        <span
          className={isOverloaded ? "bg-red-300" : "bg-sky-400"}
          style={{
            width: `${projectedPart}%`,
            backgroundImage:
              "repeating-linear-gradient(45deg, rgba(255,255,255,.6) 0 2px, transparent 2px 4px)",
          }}
        />
        {/* Held back on purpose: it reads as neither taken nor available. */}
        <span
          className="bg-slate-300"
          style={{ width: `${reservedPart}%` }}
          title="Réserve hebdomadaire"
        />
      </div>
    </div>
  );
}
