import { formatDays } from "@/lib/dates";

interface TotalCellProps {
  value: number;
  isAlert?: boolean;
  isStrong?: boolean;
  className?: string;
}

/** Cellule de total, en bas de colonne ou en fin de ligne. */
export function TotalCell({
  value,
  isAlert,
  isStrong,
  className = "",
}: TotalCellProps) {
  return (
    <td
      data-alert={isAlert ? "true" : undefined}
      className={[
        "h-9 w-9 border-r border-b border-slate-400/70 text-center text-sm",
        isAlert ? "bg-red-100 text-red-800 font-semibold" : "bg-slate-100",
        isStrong ? "font-semibold" : "",
        className,
      ].join(" ")}
    >
      {formatDays(value)}
    </td>
  );
}
