"use client";

import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { Button } from "@/components/ui/button";
import type { ProjectUpdateResponse } from "@/lib/api/generated/model";
import { depuis } from "@/lib/dates-relatives";

interface ProjectUpdateCardProps {
  maj: ProjectUpdateResponse;
  maintenant: Date;
  onEdit: (body: string) => Promise<void>;
  onRemove: () => Promise<void>;
}

/**
 * Une mise a jour du fil.
 *
 * Retiree, elle garde sa place et sa signature : le fil raconte qu'il s'est
 * passe quelque chose, et les reponses qu'elle a suscitees gardent leur
 * contexte. Seul son texte disparait.
 */
export function ProjectUpdateCard({
  maj,
  maintenant,
  onEdit,
  onRemove,
}: ProjectUpdateCardProps) {
  const [enEdition, setEnEdition] = useState(false);

  return (
    <article className="rounded-lg border border-slate-300 bg-white p-3">
      <header className="mb-2 flex items-center gap-2">
        <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
          {maj.author.initials}
        </span>
        <span className="text-sm font-medium text-slate-800">
          {maj.author.display_name}
        </span>
        <span className="text-xs text-slate-400">
          {depuis(maj.published_at, maintenant)}
          {maj.edited_at && !maj.is_deleted && " · modifiée"}
        </span>

        {maj.is_mine && !maj.is_deleted && !enEdition && (
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

      {maj.is_deleted ? (
        <p className="text-sm text-slate-400 italic">Message supprimé</p>
      ) : enEdition ? (
        <Correction
          value={maj.body}
          onCancel={() => setEnEdition(false)}
          onSave={async (body) => {
            await onEdit(body);
            setEnEdition(false);
          }}
        />
      ) : (
        <MarkdownView body={maj.body} />
      )}
    </article>
  );
}

/** Correction d'une mise a jour, en place dans le fil. */
function Correction({
  value,
  onSave,
  onCancel,
}: {
  value: string;
  onSave: (body: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [body, setTexte] = useState(value);

  return (
    <div className="space-y-2">
      <RichTextEditor
        value={value}
        onChange={setTexte}
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
