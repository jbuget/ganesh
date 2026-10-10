"use client";

import { ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";

import type { Verdict } from "@/lib/api/generated/model";

interface AnswerVerdictProps {
  verdict: Verdict | null;
  onJudge: (verdict: Verdict) => void;
}

const CHOICES = [
  {
    verdict: "helpful",
    label: "Réponse utile",
    Icon: ThumbsUp,
    chosen: "text-emerald-600",
    spring: "verdict-up",
  },
  {
    verdict: "unhelpful",
    label: "Réponse pas utile",
    Icon: ThumbsDown,
    chosen: "text-red-600",
    spring: "verdict-down",
  },
] as const;

/**
 * Whether an answer helped, in one click.
 *
 * What turns the exchanges kept into a sample worth reading: the answers
 * somebody said were no use are the ones to study first.
 *
 * The thumb clicked springs once — up for the one, down for the other — and
 * keeps its colour. Only a click springs it: a verdict drawn again when the
 * panel comes back was given earlier, and celebrating it twice would be noise.
 */
export function AnswerVerdict({ verdict, onJudge }: AnswerVerdictProps) {
  const [springing, setSpringing] = useState<Verdict | null>(null);

  return (
    <div className="flex gap-0.5">
      {CHOICES.map(({ verdict: choice, label, Icon, chosen, spring }) => (
        <button
          key={choice}
          type="button"
          aria-label={label}
          aria-pressed={verdict === choice}
          onClick={() => {
            setSpringing(choice);
            onJudge(choice);
          }}
          onAnimationEnd={() => setSpringing(null)}
          className={`cursor-pointer rounded-full p-1 transition-colors hover:bg-slate-100 ${
            verdict === choice ? chosen : "text-slate-400 hover:text-slate-700"
          } ${springing === choice ? spring : ""}`}
        >
          <Icon
            className="size-3.5"
            strokeWidth={verdict === choice ? 2.5 : 2}
            aria-hidden
          />
        </button>
      ))}
    </div>
  );
}
