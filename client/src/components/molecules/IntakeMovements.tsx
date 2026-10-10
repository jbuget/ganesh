import { CountBar } from "@/components/atoms/CountBar";
import type { IntakeResponse } from "@/lib/api/generated/model";
import { intakeRows } from "@/lib/statistics";

interface IntakeMovementsProps {
  intake: IntakeResponse;
}

/**
 * What the company asked for over the window, and what became of it.
 *
 * Asked, answered, built — and not a funnel: a need accepted today may have
 * been handed over last month, so no line is a share of the first. A month
 * that filed six and built none says something neither figure says alone.
 */
export function IntakeMovements({ intake }: IntakeMovementsProps) {
  const rows = intakeRows(intake);
  const max = Math.max(0, ...rows.map((row) => row.count));

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-medium text-slate-900">Mouvements de la période</h3>

      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">
          Aucun besoin déposé ni arbitré sur la période.
        </p>
      ) : (
        <div className="mt-3 space-y-2.5">
          {rows.map((row) => (
            <CountBar key={row.key} label={row.label} count={row.count} max={max} />
          ))}
        </div>
      )}
    </section>
  );
}
