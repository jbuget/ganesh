import { StackedBar } from "@/components/atoms/StackedBar";
import type { SteeringResponse } from "@/lib/api/generated/model";
import { tradeSegments } from "@/lib/statistics";

interface TradeSplitProps {
  steering: SteeringResponse;
}

/**
 * The project time, split by the trade it was booked under.
 *
 * What states no trade is drawn as a part of its own rather than left out:
 * it is the days the reprise took over, and the size of that part says how
 * far the reading can be trusted.
 */
export function TradeSplit({ steering }: TradeSplitProps) {
  const segments = tradeSegments(steering);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 sm:col-span-2">
      <h3 className="text-sm font-medium text-slate-900">Temps par métier</h3>

      {segments.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">Aucune saisie sur la période.</p>
      ) : (
        <div className="mt-3">
          <StackedBar segments={segments} label="Temps de projet par métier" />
        </div>
      )}
    </section>
  );
}
