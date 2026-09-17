"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { Button } from "@/components/ui/button";

interface ProjectSheetTabProps {
  description: string | null;
  onSave: (texte: string) => Promise<void>;
}

/** Redaction de la fiche, avec les titres qui l'articulent. */
function Redaction({
  valeur,
  onSave,
  onCancel,
}: {
  valeur: string;
  onSave: (texte: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [texte, setTexte] = useState(valeur);
  const [enCours, setEnCours] = useState(false);

  async function enregistrer() {
    setEnCours(true);
    try {
      await onSave(texte);
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <RichTextEditor
        valeur={valeur}
        avecTitres
        pleineHauteur
        placeholder="Le problème, la solution, ce que le service couvre…"
        onChange={setTexte}
        onSubmit={() => void enregistrer()}
      />
      <div className="flex shrink-0 items-center gap-2">
        <Button size="sm" disabled={enCours} onClick={() => void enregistrer()}>
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

/**
 * La fiche de service d'une mission.
 *
 * On la lit bien plus souvent qu'on ne l'ecrit : elle s'affiche rendue, et
 * l'editeur ne s'ouvre qu'a la demande. Il montre la mise en forme pendant la
 * frappe, mais ce qui part en base reste du markdown — c'est lui qui nourrira
 * les fiches publiques.
 */
export function ProjectSheetTab({ description, onSave }: ProjectSheetTabProps) {
  const [enEdition, setEnEdition] = useState(false);

  if (enEdition) {
    return (
      <Redaction
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
