"use client";

import { useState } from "react";

import { formatWeek } from "@/lib/dates";
import { NOTHING, formatPersonDays, formatShare } from "@/lib/statistics";

/** One week of the curve: its Monday, and its coverage when it expected any. */
export interface CurvePoint {
  weekStart: string;
  rate: number | null | undefined;
  /** The person-days behind the rate, said in the detail of the week. */
  declaredDays: number;
  expectedDays: number;
}

interface CoverageCurveProps {
  points: CurvePoint[];
}

const WIDTH = 600;
const HEIGHT = 132;
const PAD = { left: 38, right: 10, top: 8, bottom: 22 };
const SERIES = "#2a78d6";

/**
 * The coverage week by week: where the team stands, and where it is going.
 *
 * One series on one axis, so no legend box: the heading names it. The scale
 * always holds a hundred per cent — a curve zoomed on 80–90 would make a
 * dip of two points look like a collapse. An excess raises the ceiling
 * rather than being cut.
 *
 * A week that expected nobody is a gap in the line, never a zero: joining
 * across a holiday week would draw a fall that never happened.
 *
 * Over a week the pointer draws a rule and opens its detail: the rate and the
 * person-days behind it. The figures are also held as a table for whoever
 * cannot see the line.
 */
export function CoverageCurve({ points }: CoverageCurveProps) {
  const [active, setActive] = useState<number | null>(null);

  const known = points.filter((point) => point.rate != null);
  if (known.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        Aucune semaine n&apos;attendait de saisie.
      </p>
    );
  }

  const ceiling = Math.max(1, ...known.map((point) => point.rate ?? 0));
  const plotWidth = WIDTH - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const x = (index: number) =>
    PAD.left +
    (points.length === 1 ? plotWidth / 2 : (index * plotWidth) / (points.length - 1));
  const y = (rate: number) => PAD.top + (1 - rate / ceiling) * plotHeight;

  const lines = runsOf(points).map((run) =>
    run.map(({ point, index }) => `${x(index)},${y(point.rate ?? 0)}`).join(" L"),
  );
  const first = known[0];
  const last = known[known.length - 1];
  const lastIndex = points.indexOf(last);
  const step = points.length === 1 ? plotWidth : plotWidth / (points.length - 1);
  const hovered = active === null ? null : points[active];

  return (
    <div className="relative">
      <svg
        onMouseLeave={() => setActive(null)}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`Couverture par semaine sur ${points.length} semaines : de ${formatShare(first.rate)} à ${formatShare(last.rate)}`}
        className="h-auto w-full"
      >
        {[0, 0.5, 1].map((level) => (
          <g key={level}>
            <line
              x1={PAD.left}
              x2={WIDTH - PAD.right}
              y1={y(level)}
              y2={y(level)}
              className="stroke-slate-200"
              strokeWidth={1}
            />
            <text
              x={PAD.left - 6}
              y={y(level)}
              textAnchor="end"
              dominantBaseline="middle"
              className="fill-slate-500 text-[10px]"
            >
              {formatShare(level)}
            </text>
          </g>
        ))}

        {lines.map((line) => (
          <path
            key={line}
            data-line
            d={`M${line}`}
            fill="none"
            stroke={SERIES}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ))}

        {/* The last week carries the marker, with a ring in the surface
            colour so it reads over the line. */}
        <circle
          cx={x(lastIndex)}
          cy={y(last.rate ?? 0)}
          r={4}
          fill={SERIES}
          stroke="white"
          strokeWidth={2}
        />

        {active !== null && hovered?.rate != null && (
          <>
            <line
              x1={x(active)}
              x2={x(active)}
              y1={PAD.top}
              y2={PAD.top + plotHeight}
              className="stroke-slate-300"
              strokeWidth={1}
            />
            <circle
              cx={x(active)}
              cy={y(hovered.rate)}
              r={4}
              fill={SERIES}
              stroke="white"
              strokeWidth={2}
            />
          </>
        )}

        {/* One band per week, the whole height of the plot: a target far
            larger than the mark, so the pointer never has to hit a dot. */}
        {points.map((point, index) =>
          point.rate == null ? null : (
            <rect
              key={point.weekStart}
              data-week={point.weekStart}
              x={x(index) - step / 2}
              y={PAD.top}
              width={step}
              height={plotHeight}
              fill="transparent"
              onMouseEnter={() => setActive(index)}
            />
          ),
        )}

        <text x={PAD.left} y={HEIGHT - 6} className="fill-slate-500 text-[10px]">
          {`sem. du ${formatWeek(points[0].weekStart)}`}
        </text>
        <text
          x={WIDTH - PAD.right}
          y={HEIGHT - 6}
          textAnchor="end"
          className="fill-slate-500 text-[10px]"
        >
          {`sem. du ${formatWeek(points[points.length - 1].weekStart)}`}
        </text>
      </svg>

      {active !== null && hovered?.rate != null && (
        <div
          role="tooltip"
          style={{
            // Clamped, so the card never spills over the edge of the frame.
            left: `${Math.min(86, Math.max(14, (x(active) / WIDTH) * 100))}%`,
          }}
          className="pointer-events-none absolute top-0 z-10 -translate-x-1/2 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs shadow-sm"
        >
          <p className="text-slate-500">Semaine du {formatWeek(hovered.weekStart)}</p>
          <p className="text-base font-semibold tabular-nums text-slate-900">
            {formatShare(hovered.rate)}
          </p>
          <p className="tabular-nums text-slate-600">
            {formatPersonDays(hovered.declaredDays)} /{" "}
            {formatPersonDays(hovered.expectedDays)} jours-personnes
          </p>
        </div>
      )}

      <table className="sr-only">
        <caption>Couverture de la saisie par semaine</caption>
        <tbody>
          {points.map((point) => (
            <tr key={point.weekStart}>
              <th scope="row">{formatWeek(point.weekStart)}</th>
              <td>{point.rate == null ? NOTHING : formatShare(point.rate)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** The stretches of weeks that expected something, split at every gap. */
function runsOf(points: CurvePoint[]) {
  const runs: { point: CurvePoint; index: number }[][] = [];
  points.forEach((point, index) => {
    if (point.rate == null) {
      runs.push([]);
      return;
    }
    if (runs.length === 0) runs.push([]);
    runs[runs.length - 1].push({ point, index });
  });
  return runs.filter((run) => run.length > 0);
}
