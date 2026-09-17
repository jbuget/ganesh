"use client";

import { useState } from "react";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

interface MarkdownEditorProps {
  valeur: string;
  onSave: (texte: string) => Promise<void>;
  onCancel: () => void;
}

/**
 * Redaction d'un texte markdown, ecriture et apercu.
 *
 * Deux onglets plutot qu'un apercu cote a cote : le panneau est etroit, et
 * l'on ecrit longtemps avant de relire.
 */
export function MarkdownEditor({ valeur, onSave, onCancel }: MarkdownEditorProps) {
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
    <div className="space-y-3">
      <Tabs defaultValue="ecrire" className="gap-2">
        <TabsList>
          <TabsTrigger value="ecrire">Écrire</TabsTrigger>
          <TabsTrigger value="apercu">Aperçu</TabsTrigger>
        </TabsList>

        <TabsContent value="ecrire">
          <Textarea
            value={texte}
            rows={16}
            autoFocus
            placeholder={"## Problème\n\n…\n\n## Solution\n\n…"}
            onChange={(event) => setTexte(event.target.value)}
            // Le raccourci des formulaires longs : on enregistre sans relacher
            // le clavier pour aller chercher un bouton.
            onKeyDown={(event) => {
              if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                void enregistrer();
              }
            }}
            className="font-mono text-sm"
          />
        </TabsContent>

        <TabsContent value="apercu">
          {texte.trim() ? (
            <MarkdownView texte={texte} />
          ) : (
            <p className="py-8 text-center text-sm text-slate-400">Rien à afficher</p>
          )}
        </TabsContent>
      </Tabs>

      <div className="flex items-center gap-2">
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
