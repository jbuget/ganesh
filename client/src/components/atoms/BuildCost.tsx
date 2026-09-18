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

  // Le rapport se lit toujours en entier, « 0/20 » compris : un nombre seul
  // ne dirait pas s'il compte ce qui a ete consomme ou ce qui etait prevu, et
  // un projet dont le build precede Timesheet se lirait comme un projet
  // arrive pile sur son devis.
  return (
    <span className={cost.has_overrun ? "text-red-700" : undefined}>
      {formatDecimalDays(cost.build_days)}/{formatDecimalDays(cost.estimated_days)} jrs.
    </span>
  );
}
