"use client";

import { useState } from "react";

import { ProjectUpdateCard } from "@/components/molecules/ProjectUpdateCard";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useProjectUpdates } from "@/lib/use-project-updates";

interface ProjectUpdatesTabProps {
  projectId: number;
  /** Fige l'heure de reference : sans cela, serveur et client divergeraient. */
  maintenant: Date;
}

/**
 * Le fil de suivi d'une mission.
 *
 * La redaction est en haut et le fil antechronologique en dessous : on vient
 * pour lire ce qui est arrive depuis la derniere fois, et pour ajouter sa
 * pierre.
 */
export function ProjectUpdatesTab({ projectId, maintenant }: ProjectUpdatesTabProps) {
  const suivi = useProjectUpdates(projectId);
  const [texte, setTexte] = useState("");
  const [enCours, setEnCours] = useState(false);

  async function publier() {
    setEnCours(true);
    try {
      await suivi.publier(texte);
      setTexte("");
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Textarea
          value={texte}
          rows={3}
          placeholder="Rédigez une mise à jour…"
          onChange={(event) => setTexte(event.target.value)}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
              if (texte.trim()) void publier();
            }
          }}
          className="text-sm"
        />
        {texte.trim() && (
          <div className="flex items-center gap-2">
            <Button size="sm" disabled={enCours} onClick={() => void publier()}>
              Publier
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setTexte("")}>
              Annuler
            </Button>
            <span className="text-xs text-slate-400">⌘↵ pour publier</span>
          </div>
        )}
      </div>

      {suivi.fil === null && <p className="text-sm text-slate-400">Chargement…</p>}

      {suivi.fil?.length === 0 && (
        <p className="py-6 text-center text-sm text-slate-400">
          Aucune mise à jour. Racontez où en est la mission.
        </p>
      )}

      <div className="space-y-2">
        {suivi.fil?.map((maj) => (
          <ProjectUpdateCard
            key={maj.id}
            maj={maj}
            maintenant={maintenant}
            onEdit={(texte) => suivi.corriger(maj.id, texte)}
            onRemove={() => suivi.retirer(maj.id)}
          />
        ))}
      </div>
    </div>
  );
}
