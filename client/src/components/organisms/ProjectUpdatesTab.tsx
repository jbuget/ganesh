"use client";

import { useState } from "react";

import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { ProjectUpdateCard } from "@/components/molecules/ProjectUpdateCard";
import { Button } from "@/components/ui/button";
import { useProjectUpdates } from "@/lib/use-project-updates";

interface ProjectUpdatesTabProps {
  projectId: number;
  /** Freezes the reference time: without it, server and client would diverge. */
  maintenant: Date;
  /** Previent l'ecran d'ou l'on vient : il annonce le fil sans l'ouvrir. */
  onChange?: () => void | Promise<void>;
  /** Pose le curseur dans la redaction des l'ouverture. */
  focusRedaction?: boolean;
}

/**
 * Le fil de suivi d'une mission.
 *
 * La redaction est en haut et le fil antechronologique en dessous : on vient
 * pour lire ce qui est arrive depuis la derniere fois, et pour ajouter sa
 * pierre.
 */
export function ProjectUpdatesTab({
  projectId,
  maintenant,
  onChange,
  focusRedaction = false,
}: ProjectUpdatesTabProps) {
  const suivi = useProjectUpdates(projectId, onChange);
  const [body, setTexte] = useState("");
  const [enCours, setEnCours] = useState(false);
  // Remonter la cle vide l'editeur : son contenu vit dans ProseMirror, pas
  // dans React, et il ne se reinitialise pas en changeant une propriete.
  const [cleDeRedaction, setCleDeRedaction] = useState(0);

  async function publier() {
    setEnCours(true);
    try {
      await suivi.publier(body);
      setTexte("");
      setCleDeRedaction((cle) => cle + 1);
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <RichTextEditor
          key={cleDeRedaction}
          value=""
          placeholder="Rédigez une mise à jour…"
          autoFocus={focusRedaction}
          onChange={setTexte}
          onSubmit={() => {
            if (body.trim()) void publier();
          }}
        />
        {body.trim() && (
          <div className="flex items-center gap-2">
            <Button size="sm" disabled={enCours} onClick={() => void publier()}>
              Publier
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setTexte("");
                setCleDeRedaction((cle) => cle + 1);
              }}
            >
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
            onEdit={(body) => suivi.corriger(maj.id, body)}
            onRemove={() => suivi.retirer(maj.id)}
          />
        ))}
      </div>
    </div>
  );
}
