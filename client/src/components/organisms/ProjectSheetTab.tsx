"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { Button } from "@/components/ui/button";

interface ProjectSheetTabProps {
  description: string | null;
  onSave: (body: string) => Promise<void>;
}

/** Writing the sheet, with the headings that structure it. */
function Redaction({
  value,
  onSave,
  onCancel,
}: {
  value: string;
  onSave: (body: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [body, setTexte] = useState(value);
  const [enCours, setEnCours] = useState(false);

  async function save() {
    setEnCours(true);
    try {
      await onSave(body);
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <RichTextEditor
        value={value}
        withHeadings
        fullHeight
        placeholder="Le problème, la solution, ce que le service couvre…"
        onChange={setTexte}
        onSubmit={() => void save()}
      />
      <div className="flex shrink-0 items-center gap-2">
        <Button size="sm" disabled={enCours} onClick={() => void save()}>
          Enregistrer
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>
          Annuler
        </Button>
        <span className="text-xs text-slate-400">⌘↵ pour save</span>
      </div>
    </div>
  );
}

/**
 * A mission's service sheet.
 *
 * It is read far more often than it is written: it shows rendered, and the
 * editor only opens on demand. The editor shows the formatting while typing,
 * but what goes to the database stays markdown — that is what will feed the
 * public pages.
 */
export function ProjectSheetTab({ description, onSave }: ProjectSheetTabProps) {
  const [enEdition, setEnEdition] = useState(false);

  if (enEdition) {
    return (
      <Redaction
        value={description ?? ""}
        onCancel={() => setEnEdition(false)}
        onSave={async (body) => {
          await onSave(body);
          setEnEdition(false);
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => setEnEdition(true)}
        className="flex cursor-pointer items-center gap-1.5 text-sm text-slate-400 transition-colors hover:text-slate-700"
      >
        <Pencil className="size-3.5" aria-hidden />
        {description ? "Modifier" : "Rédiger la fiche"}
      </button>

      {description ? (
        <MarkdownView body={description} />
      ) : (
        <p className="text-sm text-slate-400">
          Aucune fiche. Décrivez le problème, la solution et ce que le service couvre.
        </p>
      )}
    </div>
  );
}
