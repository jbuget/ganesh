import { formatDays } from "@/lib/dates";

interface TotalCellProps {
  value: number;
  isAlert?: boolean;
  isStrong?: boolean;
}

/** Cellule de total, en bas de colonne ou en fin de ligne. */
export function TotalCell({ value, isAlert, isStrong }: TotalCellProps) {
  return (
    <td
      className={[
        "h-9 w-9 border-r border-b border-slate-200 text-center text-sm",
        isAlert ? "bg-red-50 text-red-700 font-semibold" : "bg-slate-50",
        isStrong ? "font-semibold" : "",
      ].join(" ")}
    >
      {formatDays(value)}
    </td>
  );
}
