"use client";

import { useState } from "react";

import { AttachmentPreviewDialog } from "@/components/atoms/AttachmentPreviewDialog";
import { DeleteAttachmentDialog } from "@/components/atoms/DeleteAttachmentDialog";
import { FileDropZone } from "@/components/atoms/FileDropZone";
import { AttachmentCard } from "@/components/molecules/AttachmentCard";
import type { ProjectAttachmentResponse } from "@/lib/api/generated/model";
import { contentUrl, downloadUrl } from "@/lib/attachments";
import { useProjectAttachments } from "@/lib/use-project-attachments";

interface ProjectAttachmentsTabProps {
  projectId: number;
  /** Tells the screen one came from that the project now carries one file more. */
  onChange?: () => void | Promise<void>;
}

/**
 * Everything a project carries besides words.
 *
 * One stock: an image pasted into an update lands here too, which is what
 * makes this tab the answer to « qu'est-ce que ce projet porte ? » rather
 * than half of it.
 */
export function ProjectAttachmentsTab({
  projectId,
  onChange,
}: ProjectAttachmentsTabProps) {
  const store = useProjectAttachments(projectId, onChange);
  const [busy, setBusy] = useState(false);
  const [shown, setShown] = useState<ProjectAttachmentResponse | null>(null);
  const [doomed, setDoomed] = useState<ProjectAttachmentResponse | null>(null);

  async function drop(files: File[]) {
    setBusy(true);
    try {
      // One after another rather than all at once: the refusal of one file
      // must not take the others down with it.
      for (const file of files) {
        try {
          await store.upload(file);
        } catch {
          // The hook holds what it was refused for; the zone says it below.
        }
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <FileDropZone onFiles={drop} busy={busy} />

      {store.error && <p className="text-xs text-red-700">{store.error}</p>}

      {store.files === null && <p className="text-sm text-slate-400">Chargement…</p>}

      {store.files?.length === 0 && (
        <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
          Aucun fichier. Déposez une capture, une maquette, un compte rendu.
        </p>
      )}

      {store.files && store.files.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {store.files.map((file) => (
            <AttachmentCard
              key={file.id}
              projectId={projectId}
              file={file}
              onOpen={() => setShown(file)}
              onRemove={() => setDoomed(file)}
            />
          ))}
        </div>
      )}

      {shown && (
        <AttachmentPreviewDialog
          open
          onOpenChange={(open) => !open && setShown(null)}
          filename={shown.filename}
          contentType={shown.content_type}
          url={contentUrl(projectId, shown.id)}
          downloadUrl={downloadUrl(projectId, shown.id)}
        />
      )}

      {doomed && (
        <DeleteAttachmentDialog
          open
          onOpenChange={(open) => !open && setDoomed(null)}
          filename={doomed.filename}
          usedInUpdates={doomed.used_in_updates}
          onConfirm={async () => {
            const going = doomed;
            setDoomed(null);
            await store.remove(going.id);
          }}
        />
      )}
    </div>
  );
}
