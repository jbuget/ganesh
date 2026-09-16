import { dayNumber, weekdayInitial } from "@/lib/dates";

interface DayHeaderProps {
  jour: string;
  isOffDay: boolean;
  isToday: boolean;
  label: string | null;
}

/**
 * En-tete d'une colonne de jour.
 *
 * Les jours non ouvres sont grises : c'est l'information que l'on doit lire au
 * premier coup d'oeil pour ne pas saisir un samedi par erreur.
 */
export function DayHeader({ jour, isOffDay, isToday, label }: DayHeaderProps) {
  return (
    <th
      scope="col"
      title={label ?? undefined}
      className={[
        "h-11 w-9 border-r border-b border-r-slate-300 border-b-slate-500",
        "text-xs font-normal",
        isOffDay
          ? "bg-slate-100 text-slate-500"
          : isToday
            ? "bg-amber-100 text-amber-900"
            : "bg-white text-slate-700",
        isToday ? "font-semibold" : "",
      ].join(" ")}
    >
      <div className="leading-tight">{weekdayInitial(jour)}</div>
      <div className="leading-tight">{dayNumber(jour)}</div>
    </th>
  );
}
