"use client";

import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { Button } from "@/components/ui/button";
import type { ProjectUpdateResponse } from "@/lib/api/generated/model";
import { since } from "@/lib/relative-dates";

interface ProjectUpdateCardProps {
  update: ProjectUpdateResponse;
  now: Date;
  onEdit: (body: string) => Promise<void>;
  onRemove: () => Promise<void>;
}

/**
 * One update from the thread.
 *
 * Withdrawn, it keeps its place and its signature: the thread still tells that
 * something happened, and the replies it drew keep their context. Only its text
 * goes.
 */
export function ProjectUpdateCard({
  update,
  now,
  onEdit,
  onRemove,
}: ProjectUpdateCardProps) {
  const [enEdition, setEnEdition] = useState(false);

  return (
    <article className="rounded-lg border border-slate-300 bg-white p-3">
      <header className="mb-2 flex items-center gap-2">
        <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
          {update.author.initials}
        </span>
        <span className="text-sm font-medium text-slate-800">
          {update.author.display_name}
        </span>
        <span className="text-xs text-slate-400">
          {since(update.published_at, now)}
          {update.edited_at && !update.is_deleted && " · modifiée"}
        </span>

        {update.is_mine && !update.is_deleted && !enEdition && (
          <span className="ml-auto flex items-center gap-0.5">
            <button
              type="button"
              aria-label="Modifier la mise à jour"
              onClick={() => setEnEdition(true)}
              className="cursor-pointer rounded p-1 text-slate-300 transition-colors hover:bg-slate-100 hover:text-slate-600"
            >
              <Pencil className="size-3.5" aria-hidden />
            </button>
            <button
              type="button"
              aria-label="Supprimer la mise à jour"
              onClick={() => void onRemove()}
              className="cursor-pointer rounded p-1 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
            >
              <Trash2 className="size-3.5" aria-hidden />
            </button>
          </span>
        )}
      </header>

      {update.is_deleted ? (
        <p className="text-sm text-slate-400 italic">Message supprimé</p>
      ) : enEdition ? (
        <Correction
          value={update.body}
          onCancel={() => setEnEdition(false)}
          onSave={async (body) => {
            await onEdit(body);
            setEnEdition(false);
          }}
        />
      ) : (
        <MarkdownView body={update.body} />
      )}
    </article>
  );
}

/** Correcting an update, in place in the thread. */
function Correction({
  value,
  onSave,
  onCancel,
}: {
  value: string;
  onSave: (body: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [body, setBody] = useState(value);

  return (
    <div className="space-y-2">
      <RichTextEditor
        value={value}
        onChange={setBody}
        onSubmit={() => void onSave(body)}
      />
      <div className="flex items-center gap-2">
        <Button size="sm" disabled={!body.trim()} onClick={() => void onSave(body)}>
          Enregistrer
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>
          Annuler
        </Button>
      </div>
    </div>
  );
}
