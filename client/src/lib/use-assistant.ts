"use client";

import { useQueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { useMemo, useState } from "react";

import { askAssistant, judgeAnswer } from "@/lib/api/generated/assistant/assistant";
import type { ExchangeResponse, Verdict } from "@/lib/api/generated/model";
import {
  mutationResult,
  useAssistantStatus,
  useProjects,
  useTeammates,
} from "@/lib/api/queries";
import {
  consultedProjects,
  nameTargets,
  projectInView,
  refusalOf,
  type ConsultedProject,
} from "@/lib/assistant";
import { refreshStudy } from "@/lib/assistant-study";
import { closeAssistant, useAssistantOpen } from "@/lib/assistant-store";
import { useQueryString } from "@/lib/url-state";

/** One question and its answer, as the panel draws them. */
export interface AssistantTurn {
  id: number;
  question: string;
  /** In markdown, as the model wrote it. */
  answer: string;
  consulted: ConsultedProject[];
  verdict: Verdict | null;
}

/** What the assistant's panel knows, and what it can be asked to do. */
export interface Assistant {
  isOpen: boolean;
  close: () => void;
  /** Unknown until the panel has been opened once. */
  isAvailable: boolean | null;
  /** The project in view, which a question is asked about unless it says otherwise. */
  projectId: number | null;
  turns: AssistantTurn[];
  /** The question on its way, drawn before its answer comes back. */
  pending: string | null;
  /** Where every project and person an answer may name leads. */
  names: Map<string, string>;
  /** How many questions a conversation holds; unknown until the server says. */
  maxExchanges: number | null;
  /** How many questions the conversation still holds; unknown likewise. */
  remaining: number | null;
  isOver: boolean;
  /** Why the last question went unanswered, in the reader's words. */
  refusal: string | null;
  ask: (question: string) => Promise<void>;
  judge: (exchangeId: number, verdict: Verdict) => Promise<void>;
  /** Puts the conversation away and opens a fresh one on the next question. */
  restart: () => void;
}

/**
 * Everything the assistant's panel does, apart from being drawn.
 *
 * The conversation is held here rather than in the panel's own state: the
 * panel is put away and taken out again, and one goes from screen to screen
 * in between, but the conversation is only lost on a reload — or on purpose.
 */
export function useAssistant(): Assistant {
  const queryClient = useQueryClient();
  const isOpen = useAssistantOpen();
  const { status } = useAssistantStatus(isOpen);
  const { missions } = useProjects(true, isOpen);
  // Former teammates included: an update written by somebody who has left
  // still names them.
  const { teammates } = useTeammates(true, isOpen);
  const projectId = projectInView(usePathname(), useQueryString());

  const [exchanges, setExchanges] = useState<ExchangeResponse[]>([]);
  const [pending, setPending] = useState<string | null>(null);
  const [refusal, setRefusal] = useState<string | null>(null);

  const names = useMemo(
    () =>
      nameTargets(
        missions.map((mission) => mission.project),
        teammates,
      ),
    [missions, teammates],
  );

  const latest = exchanges.at(-1);
  // Read from the server, never assumed here: the cap is the domain's.
  const maxExchanges = status?.max_exchanges ?? null;
  const remaining = latest?.remaining ?? maxExchanges;

  async function ask(question: string) {
    setPending(question);
    setRefusal(null);
    try {
      const response = await askAssistant({
        question,
        conversation_id: latest?.conversation_id ?? null,
        project_id: projectId,
      });
      const exchange = mutationResult<ExchangeResponse>(response);
      setExchanges((held) => [...held, exchange]);
      void refreshStudy(queryClient);
    } catch (error) {
      setRefusal(refusalOf(error));
    } finally {
      setPending(null);
    }
  }

  function mark(exchangeId: number, verdict: Verdict | null) {
    setExchanges((held) =>
      held.map((exchange) =>
        exchange.id === exchangeId ? { ...exchange, verdict } : exchange,
      ),
    );
  }

  /**
   * Shown at once, kept afterwards: a thumb that waited for the round trip to
   * take its colour would spring grey. Taken back if the server did not keep
   * it — a colour on screen must say what was recorded.
   */
  async function judge(exchangeId: number, verdict: Verdict) {
    const before =
      exchanges.find((exchange) => exchange.id === exchangeId)?.verdict ?? null;
    mark(exchangeId, verdict);
    try {
      await judgeAnswer(exchangeId, { verdict });
      void refreshStudy(queryClient);
    } catch {
      mark(exchangeId, before);
    }
  }

  return {
    isOpen,
    close: closeAssistant,
    isAvailable: status?.is_available ?? null,
    projectId,
    turns: exchanges.map((exchange) => ({
      id: exchange.id,
      question: exchange.question,
      answer: exchange.answer,
      consulted: consultedProjects(exchange.consulted_project_ids, missions),
      verdict: exchange.verdict,
    })),
    pending,
    names,
    maxExchanges,
    remaining,
    isOver: remaining !== null && remaining <= 0,
    refusal,
    ask,
    judge,
    restart() {
      setExchanges([]);
      setRefusal(null);
    },
  };
}
