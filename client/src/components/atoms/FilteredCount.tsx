"use client";

interface FilteredCountProps {
  /** Rows kept, and rows one would see with no criterion. */
  visible: number;
  total: number;
  /** What is being counted, singular and plural: « mission », « missions ». */
  one: string;
  many: string;
}

/**
 * What is seen, against what could be seen.
 *
 * A nearly empty screen must explain itself: without this count, a filter that
 * keeps two rows out of forty reads as a list with two rows in it.
 *
 * It is spoken aloud: a filter that leaves nothing cannot be seen when one is
 * not looking at the screen, and `status` announces it without interrupting
 * typing.
 */
export function FilteredCount({ visible, total, one, many }: FilteredCountProps) {
  return (
    <p role="status" className="text-sm tabular-nums text-slate-500">
      {visible} {visible > 1 ? many : one} sur {total}
    </p>
  );
}
