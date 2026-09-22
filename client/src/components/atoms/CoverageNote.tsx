import { NOTHING, formatPersonDays, formatShare } from "@/lib/statistics";

interface CoverageNoteProps {
  coverage: number | null | undefined;
  declaredDays: number;
  expectedDays: number;
  /** Teammates the window expected something of, who declared nothing. */
  silent: string[];
  /**
   * How many the window expects nothing of at all.
   *
   * Counted, never named: a rhythm says how much of a week somebody works
   * and never why. The figure is here so that nobody away is quietly
   * forgotten — they weigh on no coverage and hold no capacity, and without
   * it nothing on this screen would say they exist.
   */
  away: number;
}

/**
 * How much of the expected time these figures rest on.
 *
 * It opens the screen rather than closing it, and that placement is the whole
 * point: read against a coverage of 60 %, every figure below is a costly
 * fiction. Naming those who declared nothing is deliberate — a coverage only
 * moves when someone knows it is theirs to move.
 */
export function CoverageNote({
  coverage,
  declaredDays,
  expectedDays,
  silent,
  away,
}: CoverageNoteProps) {
  const known = coverage !== null && coverage !== undefined;
  // Below this, the matrix says more about who filled in their month than
  // about where the time went.
  const thin = known && coverage < 0.8;

  return (
    <section
      className={`rounded-lg border px-4 py-3 ${
        thin ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-white"
      }`}
    >
      <p className="text-sm text-slate-700">
        <span className="font-semibold tabular-nums">
          {known ? formatShare(coverage) : NOTHING}
        </span>{" "}
        du temps attendu est déclaré sur la période —{" "}
        <span className="tabular-nums">{formatPersonDays(declaredDays)}</span> jour
        {declaredDays >= 2 ? "s" : ""} sur{" "}
        <span className="tabular-nums">{formatPersonDays(expectedDays)}</span>.
      </p>

      {away > 0 && (
        <p className="mt-1 text-sm text-slate-500">
          {away === 1
            ? "1 collaborateur sans jour attendu sur la période."
            : `${away} collaborateurs sans jour attendu sur la période.`}
        </p>
      )}

      {silent.length > 0 && (
        <p className="mt-1 text-sm text-slate-500">
          {silent.length === 1
            ? "N'a rien déclaré : "
            : `N'ont rien déclaré (${silent.length}) : `}
          {silent.join(", ")}.
        </p>
      )}
    </section>
  );
}
