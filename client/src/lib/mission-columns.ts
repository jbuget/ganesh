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
 * The line that detaches the name from the thread, and the thread from what
 * scrolls.
 *
 * It only runs along the rows, never the header: as in Monday, it starts below
 * the column name. A bar reaching the top would cut the title band in two.
 *
 * An inner shadow rather than a border: the table collapses its borders, and a
 * collapsed border belongs to the table rather than to the cell — it would
 * stay behind while the pinned column does not move. The shadow follows the
 * cell.
 */
export const SEPARATOR = "shadow-[inset_-1px_0_0_var(--color-slate-200)]";

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
  "w-[1500px] table-fixed border-separate border-spacing-0 [&_tbody_td]:border-b [&_tbody_td]:border-slate-200";
