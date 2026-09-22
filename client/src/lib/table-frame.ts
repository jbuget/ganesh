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
 * The window a table is read through, when it scrolls inside its own box.
 *
 * A frame carried by the cells closes a table that is read whole. A table
 * wider and taller than the room it has is not: its right edge and its bottom
 * sit somewhere off screen, and what one actually sees is content cut raw at
 * the viewport — the rule on the left, nothing on the other three sides.
 *
 * So the frame moves to what is fixed: the window. It stays closed whatever
 * the scroll position, and the table underneath draws only what divides it.
 * The « Feuille de route » already reads this way, in plain elements; the
 * planning reads it through a `<table>`, and both close at the same weight.
 *
 * Put it on the element that scrolls, with `TABLE_SPREAD` on the table it
 * holds. A window is a scrolling region a keyboard has to be able to reach:
 * it takes `tabIndex={0}` and a name of its own, since a grid of figures
 * holds nothing focusable of its own to arrow through.
 */
export const TABLE_WINDOW = `overflow-auto border bg-white ${STRONG_RULE}`;

/**
 * The table inside that window: as wide as what it holds, never narrower than
 * the window itself.
 *
 * `w-max` alone leaves a short horizon floating in a box it does not fill;
 * `min-w-full` alone would squeeze the weeks. The shadcn container is held
 * open besides, or it would scroll on its own account and keep the pinned
 * header inside the table.
 */
export const TABLE_SPREAD =
  "w-max min-w-full [&_[data-slot=table-container]]:overflow-visible";

/**
 * What divides a table whose frame is carried by its window.
 *
 * The faint lines alone, and none under the last row: the window closes the
 * table, so a rule there would double it.
 */
export const TABLE_LINES = [
  "[&_tbody_td]:border-b [&_tbody_td]:border-b-slate-200",
  "[&_tbody_tr:last-child_td]:border-b-0",
].join(" ");
