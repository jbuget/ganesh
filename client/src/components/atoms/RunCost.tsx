import type { ProjectCostResponse } from "@/lib/api/generated/model";
import { formatDecimalDays } from "@/lib/dates";

interface RunCostProps {
  cost: ProjectCostResponse;
}

/**
 * What a mission costs to keep alive, since it went live.
 *
 * The total alone would favour the oldest services: whoever has run longest
 * has consumed most. The pace says what it costs today, and lets two services
 * of different ages be compared. It only appears once the mission has run long
 * enough for the division to mean something.
 */
export function RunCost({ cost }: RunCostProps) {
  if (cost.run_days === 0 && cost.monthly_run_rate == null) return null;

  return (
    <span>
      {formatDecimalDays(cost.run_days)} jrs.
      {cost.monthly_run_rate != null && (
        <span className="text-slate-400">
          {" · "}
          {formatDecimalDays(cost.monthly_run_rate)} j/mois
        </span>
      )}
    </span>
  );
}
