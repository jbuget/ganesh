/**
 * How a search field is drawn, wherever one is.
 *
 * Two of them exist and cannot share a component: the one on a filter bar is
 * an atom, and so is the criterion whose panel carries the other — an atom
 * never imports an atom. Written here instead, as `table-frame.ts` does for
 * the tables, so that two fields doing the same job cannot drift into looking
 * like two kinds of control.
 *
 * The border is the one the filter criteria carry, and not the primitive's
 * lighter default: a shade between them reads as a difference in kind.
 */
export const SEARCH_FIELD = "h-9 border-slate-300 bg-white pl-8 hover:border-slate-400";

/**
 * The magnifier laid over it.
 *
 * Decorative — the field already says what it is — and letting the click
 * through to the field behind it.
 */
export const SEARCH_ICON =
  "pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-slate-400";
