/**
 * One row of a sheet: its heading on the left, its value on the right.
 *
 * Fields stack rather than arrange themselves in columns: a sheet is scanned
 * top to bottom, and a constant heading width gives that scan something to lean
 * on. Shared by the steering tab and the service sheet, so the two read alike.
 */
export function SheetRow({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 py-1.5">
      <span className="w-36 shrink-0 pt-0.5 text-sm text-slate-500">{title}</span>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
