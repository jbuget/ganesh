import { dayNumber, weekdayInitial } from "@/lib/dates";

interface DayHeaderProps {
  day: string;
  isOffDay: boolean;
  isToday: boolean;
  /** Un jour non ouvre se reduit a une bande, sauf s'il porte une saisie. */
  isNarrow?: boolean;
  /** La derniere colonne de jours porte le trait qui la separe des totaux. */
  isLastDay?: boolean;
  label: string | null;
}

/**
 * En-tete d'une colonne de jour.
 *
 * Les jours non ouvres sont grises et reduits a une bande : on ne peut pas y
 * saisir, et leur rendre toute une colonne coutait un cinquieme de la largeur
 * du tableau. Le rythme des semaines reste lisible.
 */
export function DayHeader({
  day,
  isOffDay,
  isToday,
  isNarrow = false,
  isLastDay = false,
  label,
}: DayHeaderProps) {
  const intitule = `${weekdayInitial(day)} ${dayNumber(day)}`;

  return (
    <th
      scope="col"
      title={label ?? intitule}
      className={[
        "h-11 border-t border-r border-b border-t-slate-500 border-b-slate-300 text-xs font-normal",
        isNarrow ? "w-2.5" : "w-9",
        isLastDay ? "border-r-slate-500" : "border-r-slate-300",
        isOffDay
          ? "bg-slate-100 text-slate-500"
          : isToday
            ? "bg-amber-100 text-amber-900"
            : "bg-white text-slate-700",
        isToday ? "font-semibold" : "",
      ].join(" ")}
    >
      {isNarrow ? (
        // Reduite a une bande, la colonne garde son intitule pour la lecture
        // d'ecran : une colonne anonyme rendrait le tableau incomprehensible.
        <span className="sr-only">{intitule}</span>
      ) : (
        <>
          <div className="leading-tight">{weekdayInitial(day)}</div>
          <div className="leading-tight">{dayNumber(day)}</div>
        </>
      )}
    </th>
  );
}
