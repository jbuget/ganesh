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
  focusComposer?: boolean;
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
  focusComposer = false,
}: ProjectUpdatesTabProps) {
  const thread = useProjectUpdates(projectId, onChange);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  // Bumping the key empties the editor: its content lives in ProseMirror, not
  // in React, and it does not reset by changing a prop.
  const [composerKey, setComposerKey] = useState(0);

  async function publish() {
    setBusy(true);
    try {
      await thread.publish(body);
      setBody("");
      setComposerKey((key) => key + 1);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <RichTextEditor
          key={composerKey}
          value=""
          placeholder="Rédigez une mise à jour…"
          autoFocus={focusComposer}
          onChange={setBody}
          onSubmit={() => {
            if (body.trim()) void publish();
          }}
        />
        {body.trim() && (
          <div className="flex items-center gap-2">
            <Button size="sm" disabled={busy} onClick={() => void publish()}>
              Publier
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setBody("");
                setComposerKey((key) => key + 1);
              }}
            >
              Annuler
            </Button>
            <span className="text-xs text-slate-400">⌘↵ pour publier</span>
          </div>
        )}
      </div>

      {thread.thread === null && <p className="text-sm text-slate-400">Chargement…</p>}

      {thread.thread?.length === 0 && (
        <p className="py-6 text-center text-sm text-slate-400">
          Aucune mise à jour. Racontez où en est le projet.
        </p>
      )}

      <div className="space-y-2">
        {thread.thread?.map((update) => (
          <ProjectUpdateCard
            key={update.id}
            update={update}
            now={now}
            onEdit={(body) => thread.edit(update.id, body)}
            onRemove={() => thread.remove(update.id)}
          />
        ))}
      </div>
    </div>
  );
}
