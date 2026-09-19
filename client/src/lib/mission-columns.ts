/**
 * The two left-hand columns of the reference list, held identically by the
 * header and by the rows.
 *
 * They stay in sight when scrolling right: past the fifth column, a line of
 * dots and figures no longer says which mission it is about. The update thread
 * goes with them, because it reads against the name whose activity it reports.
 *
 * The name's width is fixed rather than left to the content: the next column
 * must know how far from the edge to sit, and `left` does not work itself out.
 * The value is the one Monday uses, where the reference list comes from.
 *
 * The classes are written in full, never assembled: Tailwind reads the source
 * as it stands, and a name built at runtime would produce no style at all.
 *
 * The table is laid out `table-fixed`, without which none of this holds: in
 * automatic layout a cell widens until it contains its text, and a sixty
 * character label would push the next column away.
 */
export const NAME_COLUMN = "sticky left-0 w-[400px] min-w-[400px]";

/**
 * A cover over the page's left margin, in front of what scrolls underneath.
 *
 * The scrolling area carries its own padding, and the table slides under it
 * without stopping: without this cover, cells would be seen passing to the
 * left of the pinned column.
 *
 * It takes the page background, not the row's: the margin is not the row, and
 * tinting it on hover would spill the line outside the table.
 *
 * It stops one pixel short of the cell: flush against it, it painted over the
 * left edge of the frame, which the pinned column carries.
 */
export const LEFT_MARGIN =
  "before:absolute before:inset-y-0 before:right-[calc(100%+1px)] before:z-10 before:w-6 before:bg-slate-50";

export const THREAD_COLUMN = "sticky left-[400px] w-12 min-w-12";

/**
 * The line that detaches the name from the thread.
 *
 * It only runs along the rows, never the header: it separates two columns, and
 * a bar reaching the top would cut the title band in two.
 *
 * A border on the cell, not an inner shadow: an inset shadow stops at the
 * padding edge, so the row's bottom border cut the line at every row. The
 * table lays its borders out separately, and a cell's own border follows it
 * when the column stays pinned.
 */
export const SEPARATOR = "border-r border-r-slate-200";

/**
 * The line that closes the pinned part, where the table starts scrolling.
 *
 * It is drawn strong, and over the full height, title band included: it does
 * not separate two columns like its neighbour, it says where what stays in
 * sight stops and what slides underneath begins. Same tint as the strong rules
 * of the entry grid, so both tables mark a boundary the same way.
 */
export const STRONG_SEPARATOR = "border-r border-r-slate-500";

/**
 * The width of the following columns, set once and for all on the header: in
 * `table-fixed`, the first row decides for the whole table.
 *
 * The last one gets none: it absorbs what remains when the screen is wider
 * than the table, so that no fixed column stretches.
 */
export const PHASE_COLUMN = "w-[150px]";
export const PRIORITY_COLUMN = "w-[120px]";
export const CATEGORY_COLUMN = "w-[210px]";
export const DAYS_COLUMN = "w-[100px]";
export const MEMBERS_COLUMN = "w-[130px]";

/**
 * The columns one may put away, in the order the table draws them.
 *
 * The name and the update thread are not among them: they are what a row is
 * read by, and a line without its name says nothing. Everything else is fair
 * game — a steering meeting reads the whole panorama, then works on four
 * columns, and the rest only takes up room.
 *
 * Each one carries its width in figures, the same one its class above writes:
 * Tailwind only reads classes spelled out in full, and the table needs the
 * number to know how wide it still is once a column has gone. The two are read
 * together, and change together.
 */
export type ColumnKey =
  | "phase"
  | "priority"
  | "category"
  | "build"
  | "run"
  | "leads"
  | "contributors"
  | "links";

export interface HideableColumn {
  key: ColumnKey;
  label: string;
  width: number;
}

export const HIDEABLE_COLUMNS: readonly HideableColumn[] = [
  { key: "phase", label: "Phase", width: 150 },
  { key: "priority", label: "Priorité", width: 120 },
  { key: "category", label: "Catégorie", width: 210 },
  { key: "build", label: "Build", width: 100 },
  { key: "run", label: "Run", width: 100 },
  { key: "leads", label: "Référents", width: 130 },
  { key: "contributors", label: "Intervenants", width: 130 },
  // The links column carries no width class: it takes what is left of the
  // table. What is left is this, and putting it away gives exactly this back.
  { key: "links", label: "Liens", width: 112 },
];

/** The name and the thread, which no choice ever takes away. */
const PINNED_WIDTH = 448;

export type HiddenColumns = ReadonlySet<ColumnKey>;

export const NO_HIDDEN_COLUMN: HiddenColumns = new Set();

/** The set a list of keys makes, so callers never build one by hand. */
export function hiddenColumns(keys: readonly ColumnKey[]): HiddenColumns {
  return new Set(keys);
}

export function isHideable(column: string): column is ColumnKey {
  return HIDEABLE_COLUMNS.some((hideable) => hideable.key === column);
}

const HIDE_PARAMETER = "hide";

/**
 * The columns put away, as the address carries them.
 *
 * What is written down is what one has taken away, not what is left: a bare
 * address then shows the whole panorama, which is what one comes to the
 * reference list for.
 */
export function readHiddenColumns(params: URLSearchParams): HiddenColumns {
  const hidden = params.get(HIDE_PARAMETER);
  if (!hidden) return NO_HIDDEN_COLUMN;

  return new Set(hidden.split(",").filter(isHideable));
}

/** Writes the columns put away into the URL, leaving the other parameters alone. */
export function writeHiddenColumns(
  params: URLSearchParams,
  hidden: HiddenColumns,
): void {
  params.delete(HIDE_PARAMETER);
  if (hidden.size === 0) return;

  // The order of the table is what counts: two identical choices produce the
  // same address, whatever the order of the clicks.
  params.set(
    HIDE_PARAMETER,
    HIDEABLE_COLUMNS.filter(({ key }) => hidden.has(key))
      .map(({ key }) => key)
      .join(","),
  );
}

/**
 * How wide the table stands, once the columns put away are gone.
 *
 * It is measured rather than declared: `table-fixed` shares out whatever the
 * table is given, so a width left at its full span would stretch the remaining
 * columns instead of drawing the list narrower. The figure is carried inline —
 * Tailwind cannot write a class for a width only known once the address is
 * read.
 */
export function tableWidth(hidden: HiddenColumns): number {
  return HIDEABLE_COLUMNS.filter(({ key }) => !hidden.has(key)).reduce(
    (total, { width }) => total + width,
    PINNED_WIDTH,
  );
}

/**
 * The table takes its width from `tableWidth`, in figures: its columns are
 * fixed, so it has nothing to gain from stretching, and its container can size
 * itself on it — which a relative width would make circular. Past that width
 * the screen scrolls, and it is that scrolling the first two columns cross
 * without moving.
 *
 * Borders do not collapse: collapsed, they belong to the table and run from
 * edge to edge, including under the page margin, where they showed through on
 * the left while scrolling. Separated, each line belongs to its cell and stops
 * with it. The rows therefore carry none: the cells do the underlining, or
 * nothing would show.
 *
 * The frame is strong, the inner lines faint: the table then reads as one
 * block rather than as a grid trailing off into the page. It is drawn by the
 * cells at the edges and not by the table itself — a border on the table would
 * scroll away while the pinned column stays, leaving it open on its left.
 */
export const MISSIONS_TABLE = [
  "table-fixed border-separate border-spacing-0",
  // The top of the frame travels with the pinned header.
  "[&_th]:border-t [&_th]:border-t-slate-500",
  "[&_th:first-child]:border-l [&_th:first-child]:border-l-slate-500",
  "[&_th:last-child]:border-r [&_th:last-child]:border-r-slate-500",
  "[&_tbody_td]:border-b [&_tbody_td]:border-b-slate-200",
  "[&_tbody_td:first-child]:border-l [&_tbody_td:first-child]:border-l-slate-500",
  "[&_tbody_td:last-child]:border-r [&_tbody_td:last-child]:border-r-slate-500",
  // The last row closes the table, and carries the strong rule rather than the
  // line that separates two rows.
  "[&_tbody_tr:last-child_td]:border-b-slate-500",
].join(" ");
