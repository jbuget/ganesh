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
