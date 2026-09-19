import { ShareBar } from "@/components/atoms/ShareBar";
import type { BreakdownRow } from "@/lib/statistics";

interface ShareBreakdownProps {
  title: string;
  rows: BreakdownRow[];
}

/**
 * A breakdown of the declared time, one bar per line.
 *
 * An empty block says so in words: a heading over nothing reads as a screen
 * that failed to load.
 */
export function ShareBreakdown({ title, rows }: ShareBreakdownProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-medium text-slate-900">{title}</h3>

      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">Aucune saisie sur la période.</p>
      ) : (
        <div className="mt-3 space-y-2.5">
          {rows.map((row) => (
            <ShareBar
              key={row.key}
              label={row.label}
              days={row.days}
              share={row.share}
              colour={row.colour}
            />
          ))}
        </div>
      )}
    </section>
  );
}
