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
        "h-12 w-9 border-r border-b-2 border-slate-400/70 border-b-slate-400",
        "text-xs font-normal",
        isOffDay ? "bg-slate-200/70 text-slate-500" : "bg-white text-slate-700",
        isToday ? "text-sky-700 font-semibold" : "",
      ].join(" ")}
    >
      <div className="leading-tight">{weekdayInitial(jour)}</div>
      <div className="leading-tight">{dayNumber(jour)}</div>
    </th>
  );
}
