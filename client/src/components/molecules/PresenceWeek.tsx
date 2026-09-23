"use client";

import { PresenceMark } from "@/components/atoms/PresenceMark";
import { WEEKDAYS, type WeekPresence, nextDay, sayDay } from "@/lib/presence";

interface PresenceWeekProps {
  week: WeekPresence;
  /**
   * Whether the reader may change it.
   *
   * Everyone says their own week and nobody else's — false on a colleague's
   * panel, where it is still worth reading: knowing somebody is at home on
   * Wednesdays is the whole point of declaring it.
   */
  editable?: boolean;
  onChange?: (week: WeekPresence) => void;
}

/**
 * The five days of an ordinary week, and where one spends each.
 *
 * A click walks the day round: sur site, télétravail, absent. Nothing here is
 * counted anywhere — it is told to the team, not measured on the person.
 */
export function PresenceWeek({ week, editable = false, onChange }: PresenceWeekProps) {
  return (
    <ul className="flex flex-wrap gap-2">
      {WEEKDAYS.map((day) => {
        const value = week[day.key];
        const said = `${day.label} : ${sayDay(value)}`;

        const inside = (
          <>
            <PresenceMark day={value} size="md" labelled={false} />
            <span className="text-xs font-medium text-slate-900">{day.label}</span>
            <span className="text-[11px] text-slate-500">{sayDay(value)}</span>
          </>
        );
        const shell =
          "flex min-w-[76px] flex-1 flex-col items-center gap-1.5 rounded-md border border-slate-200 px-2 py-2.5";

        return (
          <li key={day.key} className="flex-1">
            {editable ? (
              <button
                type="button"
                title={`${said}. Cliquer pour changer.`}
                aria-label={`${said}. Cliquer pour changer.`}
                onClick={() => onChange?.({ ...week, [day.key]: nextDay(value) })}
                className={`${shell} w-full cursor-pointer transition-colors hover:border-slate-400`}
              >
                {inside}
              </button>
            ) : (
              <div title={said} aria-label={said} className={shell}>
                {inside}
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
