import { TrendBadge } from "@/components/atoms/TrendBadge";
import type { CoverageResponse } from "@/lib/api/generated/model";
import { NOTHING, formatDelay, formatPersonDays, formatShare } from "@/lib/statistics";

interface CoverageHeadlineProps {
  coverage: CoverageResponse;
  /** Median delay between a day worked and the entry declaring it. */
  medianDelay: number | null | undefined;
}

/**
 * The lead figure: how much of the expected time was actually declared.
 *
 * The median delay sits with it rather than in a block of its own, and that
 * placement is the whole point. A coverage of 95 % filled in day to day is an
 * asset to steer on; the same 95 % caught up at month end is an administrative
 * fiction. Neither figure is worth reading without the other.
 */
export function CoverageHeadline({ coverage, medianDelay }: CoverageHeadlineProps) {
  const rate = coverage.rate;
  const known = rate !== null && rate !== undefined;
  // An excess is reported as it stands, but the bar stops at its own width.
  const width = known ? Math.min(100, Math.round(rate * 100)) : 0;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="text-xs font-medium tracking-wide text-slate-500 uppercase">
        Couverture de la saisie
      </h2>

      <div className="mt-2 flex items-baseline gap-3">
        <p className="text-4xl font-semibold tabular-nums text-slate-900">
          {known ? formatShare(rate) : NOTHING}
        </p>
        <TrendBadge points={coverage.delta_in_points} />
      </div>

      {known && (
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            role="meter"
            aria-label="Couverture de la saisie"
            aria-valuenow={width}
            aria-valuemin={0}
            aria-valuemax={100}
            style={{ width: `${width}%` }}
            className="h-full rounded-full bg-slate-900"
          />
        </div>
      )}

      <dl className="mt-3 space-y-0.5 text-sm text-slate-600">
        <div>
          <dt className="sr-only">Jours déclarés</dt>
          <dd className="tabular-nums">
            {formatPersonDays(coverage.declared_days)} /{" "}
            {formatPersonDays(coverage.expected_days)} jours-personnes
            {coverage.missing_days > 0 && (
              <>
                {" · "}
                {formatPersonDays(coverage.missing_days)} jours-personnes à déclarer
              </>
            )}
          </dd>
        </div>
        <div>
          <dt className="sr-only">Fraîcheur</dt>
          <dd>délai médian de saisie : {formatDelay(medianDelay)}</dd>
        </div>
      </dl>
    </section>
  );
}
