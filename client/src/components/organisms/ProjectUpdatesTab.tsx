"use client";

import { useState } from "react";

import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { ProjectUpdateCard } from "@/components/molecules/ProjectUpdateCard";
import { Button } from "@/components/ui/button";
import { useProjectUpdates } from "@/lib/use-project-updates";

interface ProjectUpdatesTabProps {
  projectId: number;
  /** Freezes the reference time: without it, server and client would diverge. */
  now: Date;
  /** Tells the screen one came from: it announces the thread without opening it. */
  onChange?: () => void | Promise<void>;
  /** Puts the cursor in the composer as soon as it opens. */
  focusRedaction?: boolean;
}

/**
 * A mission's follow-up thread.
 *
 * The composer is at the top and the reverse-chronological thread below: one
 * comes to read what has happened since last time, and to add one's own piece.
 */
export function ProjectUpdatesTab({
  projectId,
  now,
  onChange,
  focusRedaction = false,
}: ProjectUpdatesTabProps) {
  const suivi = useProjectUpdates(projectId, onChange);
  const [body, setTexte] = useState("");
  const [enCours, setEnCours] = useState(false);
  // Bumping the key empties the editor: its content lives in ProseMirror, not
  // in React, and it does not reset by changing a prop.
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

      {suivi.thread === null && <p className="text-sm text-slate-400">Chargement…</p>}

      {suivi.thread?.length === 0 && (
        <p className="py-6 text-center text-sm text-slate-400">
          Aucune mise à jour. Racontez où en est la mission.
        </p>
      )}

      <div className="space-y-2">
        {suivi.thread?.map((maj) => (
          <ProjectUpdateCard
            key={maj.id}
            maj={maj}
            now={now}
            onEdit={(body) => suivi.corriger(maj.id, body)}
            onRemove={() => suivi.remove(maj.id)}
          />
        ))}
      </div>
    </div>
  );
}
