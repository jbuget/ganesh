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
 */
export const LEFT_MARGIN =
  "before:absolute before:inset-y-0 before:right-full before:z-10 before:w-6 before:bg-slate-50";

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
 * The table carries a firm width rather than a share of the available room:
 * its columns are fixed, so it has nothing to gain from stretching, and its
 * container can size itself on it — which a relative width would make
 * circular. Past that width the screen scrolls, and it is that scrolling the
 * first two columns cross without moving.
 *
 * Borders do not collapse: collapsed, they belong to the table and run from
 * edge to edge, including under the page margin, where they showed through on
 * the left while scrolling. Separated, each line belongs to its cell and stops
 * with it. The rows therefore carry none: the cells do the underlining, or
 * nothing would show.
 */
export const MISSIONS_TABLE =
  "w-[1500px] table-fixed border-separate border-spacing-0 [&_tbody_td]:border-b [&_tbody_td]:border-b-slate-200";
