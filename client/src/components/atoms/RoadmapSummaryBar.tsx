import { AlertTriangle, CalendarOff, CircleCheck, Rocket, Ruler } from "lucide-react";

import type { RoadmapSummaryResponse } from "@/lib/api/generated/model";

interface RoadmapSummaryBarProps {
  summary: RoadmapSummaryResponse;
}

/**
 * What the whole drawing says, above the bars.
 *
 * The first two figures are the report; the last three say how much of it to
 * believe. A roadmap of fourteen missions of which five carry no date is not
 * a roadmap of fourteen missions, and the reader has to be told so before
 * they read a single bar.
 */
export function RoadmapSummaryBar({ summary }: RoadmapSummaryBarProps) {
  const figures = [
    {
      key: "missions",
      Icon: CircleCheck,
      tone: "text-slate-400",
      value: String(summary.missions),
      label: summary.missions > 1 ? "projets" : "projet",
    },
    {
      key: "delivered",
      Icon: Rocket,
      tone: summary.delivered > 0 ? "text-emerald-600" : "text-slate-400",
      value: String(summary.delivered),
      label: summary.delivered > 1 ? "mises en service" : "mise en service",
    },
    {
      key: "late",
      Icon: AlertTriangle,
      tone: summary.late > 0 ? "text-red-600" : "text-slate-400",
      value: String(summary.late),
      label: "en retard",
    },
    {
      key: "undated",
      Icon: CalendarOff,
      tone: summary.undated > 0 ? "text-amber-500" : "text-slate-400",
      value: String(summary.undated),
      label: "sans date",
    },
    {
      key: "unestimated",
      Icon: Ruler,
      tone: summary.unestimated > 0 ? "text-amber-500" : "text-slate-400",
      value: String(summary.unestimated),
      label: "sans estimation",
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
