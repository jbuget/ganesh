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

  // Tant que rien n'est consomme, la colonne n'annonce que l'estime : sur
  // soixante lignes, autant de « 0/ » encombreraient la lecture sans rien
  // apprendre que l'absence de chiffre ne dise deja.
  if (cost.build_days === 0) {
    return <span>{formatDecimalDays(cost.estimated_days)} jrs.</span>;
  }

  return (
    <span className={cost.has_overrun ? "text-red-700" : undefined}>
      {formatDecimalDays(cost.build_days)}/{formatDecimalDays(cost.estimated_days)} jrs.
    </span>
  );
}
