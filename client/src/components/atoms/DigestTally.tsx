import type { TallyResponse } from "@/lib/api/generated/model";
import { tallyLines } from "@/lib/gazette";

interface DigestTallyProps {
  tally: TallyResponse;
}

/**
 * What the month came to, in figures.
 *
 * Every figure is an aggregate: none of them names anybody, and none of them
 * can. A count that singled a teammate out would not be a measure, and the
 * month after, nobody would fill anything in.
 */
export function DigestTally({ tally }: DigestTallyProps) {
  return (
    <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-slate-200 bg-slate-200 sm:grid-cols-5">
      {tallyLines(tally).map(({ label, value }) => (
        <div key={label} className="bg-white px-4 py-3">
          <dd className="text-xl font-semibold tabular-nums text-slate-900">{value}</dd>
          <dt className="mt-0.5 text-xs text-slate-500">{label}</dt>
        </div>
      ))}
    </dl>
  );
}
