"use client";

import { ThumbsDown, ThumbsUp } from "lucide-react";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import { ExchangeAnnotation } from "@/components/molecules/ExchangeAnnotation";
import type { Cause, StudiedExchangeResponse } from "@/lib/api/generated/model";
import { count, seconds } from "@/lib/assistant-study";
import { formatParisDateTime } from "@/lib/instants";

interface StudiedExchangeProps {
  exchange: StudiedExchangeResponse;
  askerName: (askerId: number) => string;
  projectLabel: (projectId: number) => string;
  onAnnotate: (exchangeId: number, cause: Cause, note: string) => Promise<void>;
}

/**
 * One question and its answer, with what the model was handed to write it.
 *
 * The readings are folded: they run to pages, and one opens the one that
 * explains the answer rather than scrolling past all of them.
 */
export function StudiedExchange({
  exchange,
  askerName,
  projectLabel,
  onAnnotate,
}: StudiedExchangeProps) {
  const annotatedBy = exchange.annotation?.annotated_by;

  return (
    <li className="space-y-3">
      <p className="text-xs text-slate-500">
        Question {exchange.rank} · {formatParisDateTime(exchange.asked_at)}
        {exchange.project_id !== null &&
          ` · depuis la fiche ${projectLabel(exchange.project_id)}`}
      </p>

      <p className="rounded bg-slate-100 px-3 py-2 text-sm whitespace-pre-wrap text-slate-900">
        {exchange.question}
      </p>

      <MarkdownView body={exchange.answer} images={false} />

      <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
        <span>{seconds(exchange.elapsed_ms)}</span>
        <span>
          {count(exchange.input_tokens)} tokens lus, {count(exchange.output_tokens)}{" "}
          écrits
        </span>
        <code>{exchange.model}</code>
        {exchange.verdict === "helpful" && (
          <span className="flex items-center gap-1 text-slate-700">
            <ThumbsUp aria-hidden className="size-3.5" /> Jugée utile
          </span>
        )}
        {exchange.verdict === "unhelpful" && (
          <span className="flex items-center gap-1 text-slate-700">
            <ThumbsDown aria-hidden className="size-3.5" /> Jugée pas utile
          </span>
        )}
      </p>

      <div className="space-y-1">
        <h3 className="text-xs font-medium text-slate-600">
          {exchange.consultations.length === 0
            ? "Aucun outil consulté"
            : "Ce que les outils ont lu"}
        </h3>
        {exchange.consultations.map((consultation, index) => (
          <details key={index} className="rounded border border-slate-200 text-xs">
            <summary className="cursor-pointer px-2 py-1 text-slate-700">
              <code>{consultation.tool}</code>{" "}
              <span className="text-slate-500">
                {JSON.stringify(consultation.arguments)}
              </span>
            </summary>
            <pre className="max-h-80 overflow-auto border-t border-slate-200 bg-slate-50 px-2 py-1.5 whitespace-pre-wrap text-slate-700">
              {consultation.result}
            </pre>
          </details>
        ))}
      </div>

      <ExchangeAnnotation
        key={`${exchange.id}-${exchange.annotation?.annotated_at ?? ""}`}
        exchangeId={exchange.id}
        annotation={exchange.annotation}
        annotatorName={
          annotatedBy === null || annotatedBy === undefined
            ? null
            : askerName(annotatedBy)
        }
        onAnnotate={(cause, note) => onAnnotate(exchange.id, cause, note)}
      />
    </li>
  );
}
