import { MetricTile } from "@/components/atoms/MetricTile";
import type { TallyResponse } from "@/lib/api/generated/model";
import { tallyLines } from "@/lib/gazette";

interface DigestTallyProps {
  tally: TallyResponse;
}

/**
 * What the month came to, in figures.
 *
 * Drawn in the same tiles as Statistiques: two screens showing a figure and
 * what it is called must not be able to drift apart.
 *
 * Every figure is an aggregate: none of them names anybody, and none of them
 * can. A count that singled a teammate out would not be a measure, and the
 * month after, nobody would fill anything in.
 */
export function DigestTally({ tally }: DigestTallyProps) {
  return (
    <dl className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {tallyLines(tally).map(({ label, value }) => (
        <MetricTile key={label} label={label} value={String(value)} />
      ))}
    </dl>
  );
}
