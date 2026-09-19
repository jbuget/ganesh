interface MoodAverageLineProps {
  /** One entry per day of the chart, oldest first. Null where nobody answered. */
  averages: (number | null)[];
  /** How many bands the chart has: the line is placed between their centres. */
  bands: number;
}

/** The lowest score on the scale: the bottom band. */
const LOWEST = 1;

/**
 * The mean of each day, drawn across the bands.
 *
 * It rides on top of the bubbles rather than beside them: a mean says where a
 * day settled, and that only means something against the answers it came from.
 *
 * Straight segments, not a smoothed curve: a spline invents values between two
 * days that nobody posted, and on ten points it would bend the line past the
 * means it is drawing.
 *
 * A day nobody answered breaks the line instead of pulling it down — silence
 * is not a bad day — which is why the points come out as several runs rather
 * than one.
 */
export function MoodAverageLine({ averages, bands }: MoodAverageLineProps) {
  // The line runs between the band centres, not edge to edge: a mean of five
  // belongs in the middle of the top band, where its bubbles are.
  const half = 100 / bands / 2;

  const runs: string[][] = [[]];
  averages.forEach((average, index) => {
    if (average === null) {
      runs.push([]);
      return;
    }
    const x = ((index + 0.5) / averages.length) * 100;
    // The best band sits at the top, so a higher mean rides higher.
    const y = half + ((bands - average) / (bands - LOWEST)) * (100 - 2 * half);
    runs[runs.length - 1].push(`${x},${y}`);
  });

  const lines = runs.filter((run) => run.length > 1);
  // A day answered between two silences is a run of one, and a polyline of one
  // point draws nothing: its mean would simply be missing from the chart. Drawn
  // as a dot instead — a segment doubled back on itself, which a round cap
  // renders as a disc.
  const dots = runs.filter((run) => run.length === 1);
  if (lines.length === 0 && dots.length === 0) return null;

  return (
    <svg
      // Stretched to the plot area: the stroke is kept from stretching with it,
      // which is what `vectorEffect` is for.
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      className="pointer-events-none absolute inset-0 size-full"
      aria-hidden
    >
      {lines.map((run) => (
        <polyline
          key={run[0]}
          points={run.join(" ")}
          fill="none"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
          className="stroke-slate-600"
        />
      ))}

      {dots.map(([point]) => (
        <polyline
          key={point}
          points={`${point} ${point}`}
          fill="none"
          strokeWidth={7}
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
          className="stroke-slate-600"
        />
      ))}
    </svg>
  );
}
