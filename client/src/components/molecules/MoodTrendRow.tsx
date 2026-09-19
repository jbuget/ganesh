import { MoodAverageMark } from "@/components/atoms/MoodAverageMark";
import { MoodDistributionBar } from "@/components/atoms/MoodDistributionBar";
import { TableCell, TableRow } from "@/components/ui/table";
import type { DayMoodsResponse } from "@/lib/api/generated/model";
import { formatWeekdayDate } from "@/lib/dates";
import { STRONG_SEPARATOR } from "@/lib/table-frame";

interface MoodTrendRowProps {
  day: DayMoodsResponse;
  headcount: number;
  isToday: boolean;
}

/**
 * One day of the window, summed up rather than named.
 *
 * Two readings side by side, because they answer two questions: the bar says
 * how the day was spread, the dot says where its centre fell. A day averaging
 * three with everyone at three and a day averaging three with half the team at
 * five and half at one are the same figure and not the same day.
 *
 * Nobody is named here: who said what is the record's business. Aggregating is
 * what this tab is for, and repeating the initials would make the two tabs the
 * same screen twice.
 */
export function MoodTrendRow({ day, headcount, isToday }: MoodTrendRowProps) {
  return (
    <TableRow className="group bg-slate-50 hover:bg-slate-100">
      <TableCell
        className={`bg-white py-2 group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
      >
        <span className="block text-sm text-slate-700 first-letter:uppercase">
          {formatWeekdayDate(day.day)}
        </span>
        {isToday && <span className="text-xs text-slate-400">aujourd&apos;hui</span>}
      </TableCell>

      <TableCell className="py-2 text-right text-sm tabular-nums text-slate-500">
        {day.participation}
        <span className="text-slate-300"> / {headcount}</span>
      </TableCell>

      <TableCell className="py-2">
        <MoodDistributionBar counts={day.counts} participation={day.participation} />
      </TableCell>

      <TableCell className="py-2">
        <MoodAverageMark average={day.average} />
      </TableCell>
    </TableRow>
  );
}
