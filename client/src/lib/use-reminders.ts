"use client";

import { useState } from "react";

import type { ReminderCadence, RunRemindersResponse } from "@/lib/api/generated/model";
import { runReminders } from "@/lib/api/generated/notifications/notifications";
import { ApiError } from "@/lib/api/fetcher";
import { mutationResult } from "@/lib/api/queries";

/** What the last round a manager asked for did, said in French. */
export interface RoundOutcome {
  kind: "sent" | "nothing" | "unreachable" | "refused";
  message: string;
}

/** The status the API answers with when there is nowhere to post at all. */
const NOWHERE_TO_POST = 503;

function outcomeOf(sent: number): RoundOutcome {
  if (sent === 0) {
    // Not a failure, and worth saying plainly: the round works, it simply
    // found nothing that has not already been posted.
    return {
      kind: "nothing",
      message: "Aucune lettre : personne n'a de nouveauté en attente.",
    };
  }
  return {
    kind: "sent",
    message: `${sent} lettre${sent > 1 ? "s" : ""} envoyée${sent > 1 ? "s" : ""}.`,
  };
}

function failureOf(error: unknown): RoundOutcome {
  if (error instanceof ApiError && error.status === NOWHERE_TO_POST) {
    // The answer worth having when one is testing the configuration — and the
    // reason the server refuses rather than answering « envoyée » when it has
    // nowhere to post: a green answer would move every stamp it touched, and
    // what it announced would never be announced again.
    return {
      kind: "unreachable",
      message:
        "Aucun envoi possible : le serveur d'envoi est injoignable ou mal configuré. Rien n'a été envoyé.",
    };
  }
  return {
    kind: "refused",
    message: "L'envoi n'a pas abouti. Le journal du serveur dit pourquoi.",
  };
}

/**
 * Sending a round of reminder letters by hand.
 *
 * The clock sends one a working day. This is the other way in: the morning it
 * got wrong, and the only way to see a real letter before trusting the whole
 * thing to a schedule.
 *
 * Nothing is sent twice for pressing twice — each letter moves its reader's
 * stamp as it goes — so the screen does not have to guard against it beyond
 * not asking while one round is in flight.
 */
export function useReminderRuns() {
  const [isRunning, setRunning] = useState(false);
  const [outcome, setOutcome] = useState<RoundOutcome | null>(null);

  return {
    isRunning,
    outcome,

    async run(cadence: ReminderCadence) {
      setRunning(true);
      setOutcome(null);
      try {
        const answer = mutationResult<RunRemindersResponse>(
          await runReminders({ cadence }),
        );
        setOutcome(outcomeOf(answer.sent));
      } catch (error) {
        setOutcome(failureOf(error));
      } finally {
        setRunning(false);
      }
    },
  };
}
