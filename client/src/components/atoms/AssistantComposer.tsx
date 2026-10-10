"use client";

import { SendHorizontal } from "lucide-react";
import { useState } from "react";

import { Textarea } from "@/components/ui/textarea";

interface AssistantComposerProps {
  placeholder: string;
  disabled?: boolean;
  onAsk: (question: string) => void;
}

/**
 * Where a question is typed.
 *
 * Entrée asks, as in every chat the team already uses; Maj+Entrée goes to the
 * line. Plain text: a question is not a document, and nothing pasted into it
 * is read as anything but words.
 */
export function AssistantComposer({
  placeholder,
  disabled = false,
  onAsk,
}: AssistantComposerProps) {
  const [question, setQuestion] = useState("");

  function ask() {
    const asked = question.trim();
    if (!asked || disabled) return;
    onAsk(asked);
    setQuestion("");
  }

  return (
    <div className="flex items-end gap-2">
      <Textarea
        aria-label="Votre question"
        value={question}
        placeholder={placeholder}
        disabled={disabled}
        rows={2}
        autoFocus
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={(event) => {
          if (event.key !== "Enter" || event.shiftKey) return;
          event.preventDefault();
          ask();
        }}
        className="min-h-0 resize-none"
      />
      <button
        type="button"
        aria-label="Envoyer"
        onClick={ask}
        disabled={disabled || !question.trim()}
        className="cursor-pointer rounded p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
      >
        <SendHorizontal className="size-4" aria-hidden />
      </button>
    </div>
  );
}
