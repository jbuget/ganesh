"use client";

import { useState } from "react";

import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { Button } from "@/components/ui/button";
import type { MentionablePerson } from "@/lib/mentions";

interface MessageComposerProps {
  /** What the editor opens on. Empty for a message nobody has written yet. */
  value?: string;
  placeholder?: string;
  /** The register « @ » offers, and against which a mention is read back. */
  people?: MentionablePerson[];
  /** The word on the button that sends: « Enregistrer », « Répondre ». */
  confirm: string;
  /** Puts the cursor in the editor as soon as it opens. */
  autoFocus?: boolean;
  /**
   * Where an image pasted into the editor is put down.
   *
   * One stock: a file dropped in a message is a file of the project like any
   * other, and the « Fichiers » tab lists it beside the rest.
   */
  onImageDrop?: (file: File) => Promise<string>;
  onConfirm: (body: string) => Promise<void>;
  onCancel: () => void;
}

/**
 * Writing a message of a thread, and the two ways out of it.
 *
 * One component for the three places one writes into a thread — correcting an
 * update, answering it, correcting one's answer — because they are one
 * gesture with one keyboard shortcut and one way of backing out. Written
 * three times over, they would be three chances to disagree about what ⌘↵
 * does.
 *
 * The editor is uncontrolled on purpose: its content lives in ProseMirror,
 * and handing it back a `value` on every keystroke would move the caret.
 */
export function MessageComposer({
  value = "",
  placeholder,
  people = [],
  confirm,
  autoFocus = false,
  onImageDrop,
  onConfirm,
  onCancel,
}: MessageComposerProps) {
  const [body, setBody] = useState(value);
  const [busy, setBusy] = useState(false);

  async function send() {
    if (!body.trim()) return;
    setBusy(true);
    try {
      await onConfirm(body);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <RichTextEditor
        value={value}
        placeholder={placeholder}
        mentionable={people}
        autoFocus={autoFocus}
        onImageDrop={onImageDrop}
        onChange={setBody}
        onSubmit={() => void send()}
      />
      <div className="flex items-center gap-2">
        <Button size="sm" disabled={busy || !body.trim()} onClick={() => void send()}>
          {confirm}
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>
          Annuler
        </Button>
        {/* The shortcut says the verb of the button beside it: one word to
            change, and never two that disagree. */}
        <span className="text-xs text-slate-400">⌘↵ pour {confirm.toLowerCase()}</span>
      </div>
    </div>
  );
}
