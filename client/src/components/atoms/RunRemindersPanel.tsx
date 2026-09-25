"use client";

import { Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ReminderCadence } from "@/lib/api/generated/model";
import { REMINDER_CHOICES } from "@/lib/reminders";
import { STRONG_RULE } from "@/lib/table-frame";
import { useReminderRuns } from "@/lib/use-reminders";

/** Which rounds can be sent by hand. « Jamais » is not one of them. */
const ROUNDS = REMINDER_CHOICES.filter(
  (choice) => choice.value !== ReminderCadence.NEVER,
);

/**
 * Sending a round of reminder letters by hand. Managers only.
 *
 * It sits at the foot of the inbox, and the tension is worth naming: the page
 * above is *mine*, this writes to *everybody*. It is kept apart by a rule and
 * a heading rather than moved elsewhere, because every other home would be
 * worse — the profile is personal, the teammates screen is about people, and
 * a screen of its own for one button would be furniture.
 *
 * Two buttons rather than a picker and a third: « chaque jour » and « chaque
 * semaine » are two different sets of readers, and naming the round in the
 * gesture is what stops somebody writing to the weekly readers on a Tuesday
 * by leaving a select where it was.
 */
export function RunRemindersPanel() {
  const runs = useReminderRuns();

  return (
    <section className={`mt-8 border-t pt-6 ${STRONG_RULE}`}>
      <h2 className="flex items-center gap-2 text-sm font-semibold">
        <Mail className="size-4 shrink-0 text-slate-500" aria-hidden />
        Rappels par e-mail
      </h2>

      <p className="mt-1 max-w-2xl text-sm text-slate-500">
        Ganesh envoie ces lettres tout seul, chaque jour ouvré. Les envoyer à la main
        sert à rattraper une matinée manquée, ou à vérifier la configuration avant de
        s&apos;en remettre à l&apos;horloge. Chacun ne reçoit que ce qu&apos;il n&apos;a
        pas encore lu.
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {ROUNDS.map((round) => (
          <Button
            key={round.value}
            variant="outline"
            className="cursor-pointer"
            disabled={runs.isRunning}
            onClick={() => void runs.run(round.value)}
          >
            {`Envoyer la tournée « ${round.label.toLowerCase()} »`}
          </Button>
        ))}
      </div>

      <p
        aria-live="polite"
        className={[
          "mt-2 min-h-5 text-sm",
          runs.outcome?.kind === "unreachable" || runs.outcome?.kind === "refused"
            ? "text-red-600"
            : "text-slate-500",
        ].join(" ")}
      >
        {runs.isRunning ? "Envoi en cours…" : (runs.outcome?.message ?? "")}
      </p>
    </section>
  );
}
