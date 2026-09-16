import { formatDays } from "@/lib/dates";

/** Cote d'une cellule portant un trait fort plutot que le trait de grille. */
export type StrongSide = "left" | "right" | "bottom";

interface TotalCellProps {
  value: number;
  isAlert?: boolean;
  isStrong?: boolean;
  strongSides?: StrongSide[];
}

/**
 * Cellule de total, en bas de colonne ou en fin de ligne.
 *
 * La couleur de chaque bordure est decidee ici, jamais par une classe ajoutee
 * de l'exterieur : deux classes de couleur concurrentes sur un meme cote
 * laisseraient la feuille Tailwind arbitrer, ce qui n'est pas deterministe.
 */
export function TotalCell({
  value,
  isAlert,
  isStrong,
  strongSides = [],
}: TotalCellProps) {
  const strong = new Set(strongSides);

  return (
    <td
      data-alert={isAlert ? "true" : undefined}
      className={[
        "h-9 w-9 border-r border-b text-center text-sm",
        strong.has("right") ? "border-r-slate-500" : "border-r-slate-300",
        strong.has("bottom") ? "border-b-slate-500" : "border-b-slate-300",
        strong.has("left") ? "border-l border-l-slate-500" : "",
        isAlert ? "bg-red-100 text-red-800 font-semibold" : "bg-slate-50",
        isStrong ? "font-semibold" : "",
      ].join(" ")}
    >
      {formatDays(value)}
    </td>
  );
}
