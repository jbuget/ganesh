/**
 * The heading of a section of a sheet.
 *
 * Several blocks follow one another in the same column: their title must stand
 * out from their content, otherwise one no longer sees where one stops and the
 * next begins. The rule gives the break, the weight gives the level.
 */
export function SheetSectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b border-slate-200 pb-1.5 text-sm font-semibold text-slate-900">
      {children}
    </h3>
  );
}
