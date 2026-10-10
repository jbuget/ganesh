"use client";

import { RotateCcw, X } from "lucide-react";
import { useEffect, useRef } from "react";

import { AssistantComposer } from "@/components/atoms/AssistantComposer";
import { SidePanel } from "@/components/atoms/SidePanel";
import { AssistantExchange } from "@/components/molecules/AssistantExchange";
import { useAssistantShortcut } from "@/lib/assistant-store";
import { plural } from "@/lib/plurals";
import { useAssistant } from "@/lib/use-assistant";

/**
 * The assistant, opened with ⌘J over whatever screen one is on.
 *
 * Nothing announces it yet: it is reached by whoever knows the shortcut. It
 * answers about projects, from Ganesh and nothing else, five questions to a
 * conversation.
 */
export function AssistantPanel() {
  useAssistantShortcut();
  const assistant = useAssistant();
  const end = useRef<HTMLDivElement>(null);

  const answered = assistant.turns.length;
  useEffect(() => {
    // jsdom draws nothing, and knows nothing of scrolling.
    end.current?.scrollIntoView?.({ block: "end" });
  }, [answered, assistant.pending]);

  if (!assistant.isOpen) return null;

  const started = answered > 0 || assistant.pending !== null;

  return (
    <SidePanel label="Assistant" onClose={assistant.close}>
      <header className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
        <h2 className="flex-1 text-base font-semibold text-slate-900">Assistant</h2>
        {started && (
          <button
            type="button"
            onClick={assistant.restart}
            disabled={assistant.pending !== null}
            className="flex cursor-pointer items-center gap-1.5 rounded px-2 py-1 text-xs text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RotateCcw className="size-3.5" aria-hidden />
            Nouvelle conversation
          </button>
        )}
        <button
          type="button"
          aria-label="Fermer"
          onClick={assistant.close}
          className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <X className="size-4" aria-hidden />
        </button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-5 py-4">
        {!started && (
          <p className="text-sm text-slate-500">
            Demandez où en est un projet, ce qui a bougé dessus ou qui le porte. Les
            réponses viennent de Ganesh, et de rien d&apos;autre.
          </p>
        )}

        <ol className="flex flex-col gap-6">
          {assistant.turns.map((turn) => (
            <AssistantExchange
              key={turn.id}
              turn={turn}
              names={assistant.names}
              onJudge={(id, verdict) => void assistant.judge(id, verdict)}
            />
          ))}
          {assistant.pending !== null && (
            <li className="flex flex-col gap-2">
              <p className="self-end rounded bg-slate-100 px-3 py-2 text-sm whitespace-pre-wrap text-slate-900">
                {assistant.pending}
              </p>
              <p className="animate-pulse text-sm text-slate-500">Ganesh cherche…</p>
            </li>
          )}
        </ol>

        {assistant.refusal && (
          <p role="alert" className="mt-4 text-sm text-red-700">
            {assistant.refusal}
          </p>
        )}
        <div ref={end} />
      </div>

      <footer className="flex flex-col gap-2 border-t border-slate-200 px-5 py-3">
        {assistant.isAvailable === false ? (
          <p className="text-sm text-slate-500">
            L&apos;assistant n&apos;est pas configuré sur cette instance.
          </p>
        ) : (
          <>
            {assistant.isOver ? (
              <p className="text-xs text-slate-500">
                Cette conversation est terminée. Commencez-en une nouvelle pour poser
                d&apos;autres questions.
              </p>
            ) : (
              answered > 0 &&
              assistant.remaining !== null && (
                <p className="text-xs text-slate-500">
                  {assistant.remaining} {plural(assistant.remaining, "question")}{" "}
                  {plural(assistant.remaining, "restante")}
                </p>
              )
            )}
            <AssistantComposer
              placeholder={
                assistant.projectId
                  ? "Une question sur ce projet…"
                  : "Où en est le projet… ?"
              }
              disabled={assistant.isOver || assistant.pending !== null}
              onAsk={(question) => void assistant.ask(question)}
            />
          </>
        )}
        {/* Said before anybody runs into it: a limit announced reads as a
            choice, one discovered at the fifth question reads as a fault. */}
        {assistant.maxExchanges !== null && (
          <p className="text-xs text-slate-400">
            Pour limiter les erreurs et garder des réponses pertinentes, une
            conversation compte {assistant.maxExchanges} questions au plus.
          </p>
        )}
        <p className="text-xs text-slate-400">
          Vos questions et les réponses sont conservées pour améliorer l&apos;assistant.
        </p>
      </footer>
    </SidePanel>
  );
}
