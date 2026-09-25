/**
 * How much of a month is actually filled in.
 *
 * The grid already says, day by day, whether a day adds up: green when it
 * does, red when it does not. What it did not say is how many days are still
 * waiting — and a month is validated on that, not on a sum. « 23 » declared
 * can hide two empty days and two counted twice; « 20/22 » cannot.
 *
 * The whole month is read, days still to come included. Ganesh takes forecast
 * as well as delivered time — future days are drawn dimmed and the totals tell
 * the two apart — so a day nobody has filled in yet is a day left to fill in,
 * whichever side of today it falls on. The count is a state, never a reproach:
 * it carries no alert colour.
 */

/** A day of the month, as the grid receives it. */
interface Day {
  day: string;
  is_off_day: boolean;
}

/** What was entered on a day, across every mission. */
interface DayTotal {
  day: string;
  total: number;
}

/** A day is complete when its entries add up to exactly one day. */
const A_WHOLE_DAY = 1;

/**
 * How many working days of the month add up to a whole day.
 *
 * A day carrying more than one is left out as surely as a day carrying less:
 * both are days to go back to. Non-working days are never counted — a
 * Saturday somebody declared on is inherited data the grid keeps visible, not
 * one of the days the month is measured against.
 */
export function countCompleteDays(days: Day[], totals: DayTotal[]): number {
  const entered = new Map(totals.map((total) => [total.day, total.total]));

  return days.filter((day) => !day.is_off_day && entered.get(day.day) === A_WHOLE_DAY)
    .length;
}
