"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import { MarkdownEditor } from "@/components/molecules/MarkdownEditor";

interface ProjectSheetTabProps {
  description: string | null;
  onSave: (texte: string) => Promise<void>;
}

/**
 * La fiche de service d'une mission.
 *
 * On la lit bien plus souvent qu'on ne l'ecrit : elle s'affiche rendue, et
 * l'editeur ne s'ouvre qu'a la demande.
 */
export function ProjectSheetTab({ description, onSave }: ProjectSheetTabProps) {
  const [enEdition, setEnEdition] = useState(false);

  if (enEdition) {
    return (
      <MarkdownEditor
        valeur={description ?? ""}
        onCancel={() => setEnEdition(false)}
        onSave={async (texte) => {
          await onSave(texte);
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
        <MarkdownView texte={description} />
      ) : (
        <p className="text-sm text-slate-400">
          Aucune fiche. Décrivez le problème, la solution et ce que le service couvre.
        </p>
      )}
    </div>
  );
}
