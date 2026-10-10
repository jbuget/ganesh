import {
  formatGestures,
  formatWeekdayAndDate,
  formatYearShare,
} from "@/lib/statistics";

interface ActivityDayDetailProps {
  day: string;
  gestures: number;
  /** The gestures of the busiest day of the year. */
  busiest: number;
  /** The gestures of the whole year. */
  total: number;
}

/** What the tooltip of a day says: which day, how much, and how it weighs. */
export function ActivityDayDetail({
  day,
  gestures,
  busiest,
  total,
}: ActivityDayDetailProps) {
  const isBusiest = gestures > 0 && gestures === busiest;

  return (
    <div className="min-w-44">
      <p className="text-xs text-slate-500 first-letter:uppercase">
        {formatWeekdayAndDate(day)}
      </p>
      <p className="mt-0.5 text-sm font-medium text-slate-900">
        {gestures === 0 ? "Aucun geste" : formatGestures(gestures)}
      </p>
      {gestures > 0 && (
        <p className="mt-0.5 text-xs text-slate-500">
          {isBusiest
            ? "Le jour le plus chargé de l'année"
            : `${formatYearShare(gestures, total)} de l'année`}
        </p>
      )}
    </div>
  );
}
