import type { NotificationReadingResponse } from "@/lib/api/generated/model";
import { notificationKindLabel } from "@/lib/notifications";
import { NOTHING, formatShare } from "@/lib/statistics";

interface NotificationReadRatesProps {
  reading: NotificationReadingResponse;
}

/**
 * What each kind of notification sent, and how much of it was opened.
 *
 * The least opened comes first, because it is the one a team acts on: a kind
 * that is sent and never opened is the product talking to nobody. The server
 * orders them, and the order is kept here.
 */
export function NotificationReadRates({ reading }: NotificationReadRatesProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-medium text-slate-900">Lecture par type</h3>

      {reading.kinds.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">
          Aucune notification envoyée sur la période.
        </p>
      ) : (
        <ul className="mt-3 space-y-1.5">
          {reading.kinds.map((one) => (
            <li
              key={one.kind}
              className="grid grid-cols-[1fr_auto_auto] items-center gap-x-3 text-sm"
            >
              <span className="truncate text-slate-700">
                {notificationKindLabel(one.kind)}
              </span>
              <span className="tabular-nums text-slate-500">
                {one.read} / {one.delivered}
              </span>
              <span className="w-12 text-right font-medium tabular-nums text-slate-900">
                {one.read_rate == null ? NOTHING : formatShare(one.read_rate)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
