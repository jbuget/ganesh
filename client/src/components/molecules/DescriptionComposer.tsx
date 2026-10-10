"use client";

import { useState } from "react";

import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { Button } from "@/components/ui/button";

interface DescriptionComposerProps {
  value: string;
  onSave: (body: string) => Promise<void>;
  onCancel: () => void;
}

/** Writing the body of the sheet, with the headings that structure it. */
export function DescriptionComposer({
  value,
  onSave,
  onCancel,
}: DescriptionComposerProps) {
  const [body, setBody] = useState(value);
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      await onSave(body);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <RichTextEditor
        value={value}
        withHeadings
        fullHeight
        placeholder="Le problème, la solution, ce que le service couvre…"
        onChange={setBody}
        onSubmit={() => void save()}
      />
      <div className="flex shrink-0 items-center gap-2">
        <Button size="sm" disabled={busy} onClick={() => void save()}>
          Enregistrer
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>
          Annuler
        </Button>
        <span className="text-xs text-slate-400">⌘↵ pour enregistrer</span>
      </div>
    </div>
  );
}
