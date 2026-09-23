/**
 * The frame the application's tables are drawn in.
 *
 * Borders do not collapse: collapsed, they belong to the table and run from
 * edge to edge, including under the page margin, where they showed through on
 * the left while scrolling. Separated, each line belongs to its cell and stops
 * with it. The rows therefore carry none: the cells do the underlining, or
 * nothing would show.
 *
 * The frame is strong, the inner lines faint: a table then reads as one block
 * rather than as a grid trailing off into the page. It is drawn by the cells at
 * the edges and not by the table itself — a border on the table would scroll
 * away while a pinned column stays, leaving it open on its left.
 *
 * Every table of the application reads under this same grammar: the mission
 * reference list, the entry grid, the teammates.
 */
/**
 * The colour of a strong rule: what closes a table, and never what divides it.
 *
 * Named here so that a frame drawn outside a `<table>` — the roadmap draws
 * its own, in plain elements — reads at the same weight as every other. The
 * inner lines stay faint; strength marks an edge, it does not make a grid.
 */
export const STRONG_RULE = "border-slate-500";

export const TABLE_FRAME = [
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
  // A footer carries a total, not one more row: the frame goes round it, and
  // the rule above it breaks the reading in two rather than separating two
  // lines. Tables without one are untouched.
  "[&_tfoot_td]:border-b [&_tfoot_td]:border-b-slate-500",
  "[&_tfoot_td:first-child]:border-l [&_tfoot_td:first-child]:border-l-slate-500",
  "[&_tfoot_td:last-child]:border-r [&_tfoot_td:last-child]:border-r-slate-500",
].join(" ");

/**
 * The band of titles, and the strong rule that closes it.
 *
 * Rows pass underneath: without a header staying in sight, one no longer knows
 * which column one is reading by the time one reaches the bottom. The
 * background sits on the cells and not on the row: in a table, a row's
 * background paints under the lines that scroll.
 *
 * White, where the rows take the page's tint: the titles read as the table's
 * own band rather than as a first row, and the strong rule below is what
 * carries the break.
 */
export const TABLE_HEADER =
  "sticky top-0 z-10 [&_th]:border-b [&_th]:border-b-slate-500 [&_th]:bg-white";

/**
 * The line that closes the column carrying the name.
 *
 * Strong, and over the full height, title band included: it does not separate
 * two columns, it says where what identifies a row stops and what describes it
 * begins.
 */
export const STRONG_SEPARATOR = "border-r border-r-slate-500";

/**
 * The width of the column that names the row.
 *
 * Fixed, and the same in every table, because the tables of one screen are
 * read one after the other: the teammates' accounts and their week are two
 * readings of one list, and a name column that changed width between two tabs
 * makes the whole page shift under the reader for no reason at all.
 */
export const NAMING_COLUMN = "w-[300px]";

/**
 * The cell that names the row: white, off the tinted row, one step behind it
 * on hover.
 *
 * Held here rather than written out in each table for the same reason as the
 * frame around them: two tables that read alike must not be able to drift
 * apart, and a padding or a gap typed twice eventually is.
 */
export const NAMING_CELL = `bg-white py-2 group-hover:bg-slate-50 ${STRONG_SEPARATOR}`;

/** What sits inside it: a mark, then the name, always spaced the same. */
export const NAMING_CONTENT = "flex items-center gap-2.5";

/** The name itself, which opens the row — and gives the keyboard the same way in. */
export const NAMING_BUTTON = "min-w-0 cursor-pointer truncate text-left font-medium";
