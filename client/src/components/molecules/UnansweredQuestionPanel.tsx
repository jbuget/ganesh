"use client";

import { X } from "lucide-react";

import { ConsultationReadings } from "@/components/atoms/ConsultationReadings";
import { SidePanel } from "@/components/atoms/SidePanel";
import type { UnansweredQuestionResponse } from "@/lib/api/generated/model";
import { WHY_UNANSWERED, count, seconds } from "@/lib/assistant-study";
import { formatParisDateTime } from "@/lib/instants";

interface UnansweredQuestionPanelProps {
  question: UnansweredQuestionResponse;
  askerName: string;
  projectLabel: (projectId: number) => string;
  onClose: () => void;
}

/**
 * A question left unanswered, with why and what was read before it failed.
 *
 * The readings are what explains the failure: a model that kept asking read
 * something it could not make sense of, a provider that failed did so after
 * or before the tools had their say.
 */
export function UnansweredQuestionPanel({
  question,
  askerName,
  projectLabel,
  onClose,
}: UnansweredQuestionPanelProps) {
  const why = WHY_UNANSWERED.find((held) => held.value === question.reason);

  return (
    <SidePanel label={`Question sans réponse de ${askerName}`} onClose={onClose}>
      <header className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
        <h2 className="min-w-0 flex-1 truncate text-lg font-semibold text-slate-900">
          Question sans réponse de {askerName}
        </h2>
        <button
          type="button"
          aria-label="Fermer"
          onClick={onClose}
          className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <X className="size-4" aria-hidden />
        </button>
      </header>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-5 py-4">
        <p className="text-xs text-slate-500">
          {formatParisDateTime(question.asked_at)}
          {question.project_id !== null &&
            ` · depuis la fiche ${projectLabel(question.project_id)}`}
        </p>

        <p className="rounded bg-slate-100 px-3 py-2 text-sm whitespace-pre-wrap text-slate-900">
          {question.question}
        </p>

        <p className="text-sm text-slate-700">
          <span className="font-medium">{why?.label ?? question.reason}</span>
          {why && ` — ${why.detail}`}
        </p>

        <p className="flex flex-wrap gap-x-3 text-xs text-slate-500">
          <span>{seconds(question.elapsed_ms)}</span>
          <span>
            {count(question.input_tokens)} tokens lus, {count(question.output_tokens)}{" "}
            écrits
          </span>
          <code>{question.model}</code>
        </p>

        <ConsultationReadings consultations={question.consultations} />
      </div>
    </SidePanel>
  );
}
