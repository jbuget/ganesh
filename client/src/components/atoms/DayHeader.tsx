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
        "h-12 w-9 border-r border-b border-slate-200 text-xs font-normal",
        isOffDay ? "bg-slate-100 text-slate-400" : "bg-white text-slate-600",
        isToday ? "text-sky-700 font-semibold" : "",
      ].join(" ")}
    >
      <div className="leading-tight">{weekdayInitial(jour)}</div>
      <div className="leading-tight">{dayNumber(jour)}</div>
    </th>
  );
}
