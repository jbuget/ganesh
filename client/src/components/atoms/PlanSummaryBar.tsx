import { AlertTriangle, CalendarClock, CircleCheck, UserPlus } from "lucide-react";

import type { PlanSummaryResponse } from "@/lib/api/generated/model";
import { formatDecimalDays } from "@/lib/dates";

interface PlanSummaryBarProps {
  summary: PlanSummaryResponse;
}

/**
 * What the whole projection says, in the few figures a decision turns on.
 *
 * Fifty rows say nothing at a glance. Put somebody on a mission and the count
 * of late ones moves here, under the eye, instead of hiding somewhere down the
 * table: that is what makes a scenario worth trying.
 */
export function PlanSummaryBar({ summary }: PlanSummaryBarProps) {
  const figures = [
    {
      key: "planned",
      Icon: CircleCheck,
      tone: "text-emerald-600",
      value: String(summary.planned),
      label: summary.planned > 1 ? "projets placés" : "projet placé",
    },
    {
      key: "late",
      Icon: AlertTriangle,
      tone: summary.late > 0 ? "text-red-600" : "text-slate-400",
      value: String(summary.late),
      label: summary.late > 1 ? "en retard" : "en retard",
    },
    {
      key: "unassigned",
      Icon: UserPlus,
      tone: summary.unassigned > 0 ? "text-amber-500" : "text-slate-400",
      value: String(summary.unassigned),
      label: "sans intervenant",
    },
    {
      key: "free",
      Icon: CalendarClock,
      tone: "text-slate-400",
      value: formatDecimalDays(summary.free_days),
      label: "jours disponibles",
    },
  ];

  return (
    <dl className="mb-3 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-md border border-slate-200 bg-slate-50 px-4 py-2.5">
      {figures.map(({ key, Icon, tone, value, label }) => (
        <div key={key} className="flex items-center gap-2">
          <Icon aria-hidden className={`size-4 shrink-0 ${tone}`} />
          <dd className="text-sm font-semibold text-slate-800 tabular-nums">{value}</dd>
          <dt className="text-sm text-slate-500">{label}</dt>
        </div>
      ))}
    </dl>
  );
}
