interface LogoProps {
  /** Sizing and colour come from the caller: the mark is drawn in `currentColor`. */
  className?: string;
}

/** The field the letter is drawn on: seven columns of a month's grid. */
const COLUMNS = 7;

const STEP = 64 / COLUMNS;
const CELL = STEP * 0.78;

/**
 * The cells the letter lights up, as `[column, row]`, grouped by row: the
 * literal draws on the page the G it draws on the screen.
 */
// prettier-ignore
const CELLS: ReadonlyArray<readonly [number, number]> = [
  [2, 1], [3, 1], [4, 1],
  [1, 2],
  [1, 3], [4, 3], [5, 3],
  [1, 4], [5, 4],
  [2, 5], [3, 5], [4, 5],
];

/**
 * The application's mark: a capital G drawn in the cells of a timesheet.
 *
 * A ring open between eleven o'clock and one, whose bar turns back inwards —
 * the letter and the curl of a trunk are the same gesture. The cells are the
 * product's own material: a month is a grid of days, some of them filled in.
 *
 * One cut only, the coarse one. The mark is never drawn larger than the
 * sidebar and the favicon ask for, and under 24 pixels the empty cells of a
 * finer grid stop reading as a grid and start reading as dirt.
 *
 * It is decorative: what names the application is the text beside it, and the
 * page title. Nothing here is announced twice.
 */
export function Logo({ className }: LogoProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} fill="currentColor" aria-hidden>
      {CELLS.map(([column, row]) => (
        <rect
          key={`${column}-${row}`}
          x={(column + 0.5) * STEP - CELL / 2}
          y={(row + 0.5) * STEP - CELL / 2}
          width={CELL}
          height={CELL}
          rx={CELL * 0.16}
        />
      ))}
    </svg>
  );
}
