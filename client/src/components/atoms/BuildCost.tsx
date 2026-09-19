import type { ProjectCostResponse } from "@/lib/api/generated/model";
import { formatDecimalDays } from "@/lib/dates";

interface BuildCostProps {
  cost: ProjectCostResponse;
}

/**
 * What a mission cost to build, against what it was estimated at.
 *
 * Only the build is compared to the estimate: the estimate covered the
 * construction, and a service that has been maintained for two years is not
 * late because it is still alive. Once the mission runs, the figure stops
 * moving and becomes its history.
 */
export function BuildCost({ cost }: BuildCostProps) {
  if (cost.estimated_days == null) {
    return cost.build_days > 0 ? (
      <span>{formatDecimalDays(cost.build_days)} jrs.</span>
    ) : null;
  }

  // The ratio always reads in full, « 0/20 » included: a lone figure would not
  // say whether it counts what has been spent or what was planned, and a
  // project whose build predates Ganesh would read as one that landed
  // exactly on its quote.
  return (
    <span className={cost.has_overrun ? "text-red-700" : undefined}>
      {formatDecimalDays(cost.build_days)}/{formatDecimalDays(cost.estimated_days)} jrs.
    </span>
  );
}
