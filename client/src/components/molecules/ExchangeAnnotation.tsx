"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { AnnotationResponse, Cause } from "@/lib/api/generated/model";
import { CAUSES } from "@/lib/assistant-study";
import { formatParisMoment } from "@/lib/instants";

interface ExchangeAnnotationProps {
  exchangeId: number;
  annotation: AnnotationResponse | null;
  /** Who left the annotation there, if the account still exists. */
  annotatorName: string | null;
  onAnnotate: (cause: Cause, note: string) => Promise<void>;
}

/**
 * An administrator's reading of one answer: why it came out as it did.
 *
 * A cause from a closed list, so that the readings can be counted, and a note
 * for what the cause cannot say. Saving again replaces the reading: one per
 * answer, two that disagreed would say nothing.
 */
export function ExchangeAnnotation({
  exchangeId,
  annotation,
  annotatorName,
  onAnnotate,
}: ExchangeAnnotationProps) {
  const [cause, setCause] = useState<Cause | null>(annotation?.cause ?? null);
  const [note, setNote] = useState(annotation?.note ?? "");
  const [saving, setSaving] = useState(false);

  const unchanged =
    cause === (annotation?.cause ?? null) && note.trim() === (annotation?.note ?? "");

  async function save() {
    if (cause === null) return;
    setSaving(true);
    try {
      await onAnnotate(cause, note);
    } finally {
      setSaving(false);
    }
  }

  return (
    <fieldset className="space-y-2 rounded-md border border-slate-200 p-3">
      <legend className="px-1 text-xs font-medium text-slate-600">Annotation</legend>

      <div
        role="radiogroup"
        aria-label="Cause"
        className="flex flex-wrap gap-x-4 gap-y-1"
      >
        {CAUSES.map((held) => (
          <label
            key={held.value}
            title={held.detail}
            className="flex cursor-pointer items-center gap-1.5 text-sm text-slate-700"
          >
            <input
              type="radio"
              name={`cause-${exchangeId}`}
              value={held.value}
              checked={cause === held.value}
              onChange={() => setCause(held.value)}
              className="cursor-pointer"
            />
            {held.label}
          </label>
        ))}
      </div>

      <Textarea
        aria-label="Note"
        placeholder="Ce qui s'est passé, ce qu'il faudrait changer…"
        value={note}
        onChange={(event) => setNote(event.target.value)}
        rows={2}
      />

      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-slate-500">
          {annotation
            ? `Annotée${annotatorName ? ` par ${annotatorName}` : ""} le ${formatParisMoment(annotation.annotated_at)}.`
            : "Pas encore annotée."}
        </p>
        <Button
          size="sm"
          onClick={save}
          disabled={cause === null || unchanged || saving}
          className="cursor-pointer"
        >
          Enregistrer
        </Button>
      </div>
    </fieldset>
  );
}
