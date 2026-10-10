"use client";

import { X } from "lucide-react";

import { SidePanel } from "@/components/atoms/SidePanel";
import { StudiedExchange } from "@/components/organisms/StudiedExchange";
import type { Cause, ConversationDetailResponse } from "@/lib/api/generated/model";

interface AssistantConversationPanelProps {
  /** Undefined while it is read. */
  conversation: ConversationDetailResponse | undefined;
  askerName: (askerId: number) => string;
  projectLabel: (projectId: number) => string;
  onAnnotate: (exchangeId: number, cause: Cause, note: string) => Promise<void>;
  onClose: () => void;
}

/**
 * A conversation opened for study, beside the list it was picked from.
 *
 * Every answer is shown with what the model was handed to write it: each tool
 * it asked for, what it passed, and what came back word for word. That is what
 * tells a reading the register got wrong from a sentence the model turned
 * wrong — and the annotation under the answer is where one says which.
 */
export function AssistantConversationPanel({
  conversation,
  askerName,
  projectLabel,
  onAnnotate,
  onClose,
}: AssistantConversationPanelProps) {
  const title = conversation
    ? `Conversation de ${askerName(conversation.asker_id)}`
    : "Conversation";

  return (
    <SidePanel label={title} onClose={onClose}>
      <header className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
        <h2 className="min-w-0 flex-1 truncate text-lg font-semibold text-slate-900">
          {title}
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

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
        {!conversation ? (
          <p className="text-sm text-slate-500">Chargement…</p>
        ) : (
          <ol className="space-y-8">
            {conversation.exchanges.map((exchange) => (
              <StudiedExchange
                key={exchange.id}
                exchange={exchange}
                askerName={askerName}
                projectLabel={projectLabel}
                onAnnotate={onAnnotate}
              />
            ))}
          </ol>
        )}
      </div>
    </SidePanel>
  );
}
