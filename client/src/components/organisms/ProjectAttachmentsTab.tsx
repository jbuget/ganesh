"use client";

import { useState } from "react";

import { AttachmentPreviewDialog } from "@/components/atoms/AttachmentPreviewDialog";
import { DeleteAttachmentDialog } from "@/components/atoms/DeleteAttachmentDialog";
import { FileDropZone } from "@/components/atoms/FileDropZone";
import { RenameAttachmentDialog } from "@/components/atoms/RenameAttachmentDialog";
import { AttachmentCard } from "@/components/molecules/AttachmentCard";
import type { ProjectAttachmentResponse } from "@/lib/api/generated/model";
import { useProjectAttachments } from "@/lib/use-project-attachments";

interface ProjectAttachmentsTabProps {
  projectId: number;
  /** Tells the screen one came from that the project now carries one file more. */
  onChange?: () => void | Promise<void>;
  /**
   * Whether the reader may add to the stock, or only read it.
   *
   * Opening a file stays: reading what a project carries is reading the
   * project. What goes is dropping, renaming and withdrawing.
   */
  editable?: boolean;
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
  editable = true,
}: ProjectAttachmentsTabProps) {
  const store = useProjectAttachments(projectId, onChange);
  // Only what the screen itself is: which file is open, which one is being
  // asked about. Everything a drop involves lives in the hook.
  const [shown, setShown] = useState<ProjectAttachmentResponse | null>(null);
  const [renamed, setRenamed] = useState<ProjectAttachmentResponse | null>(null);
  const [doomed, setDoomed] = useState<ProjectAttachmentResponse | null>(null);

  return (
    <div className="space-y-4">
      {editable && <FileDropZone onFiles={store.uploadAll} busy={store.busy} />}

      {store.error && <p className="text-xs text-red-700">{store.error}</p>}

      {store.files === null && <p className="text-sm text-slate-400">Chargement…</p>}

      {store.files?.length === 0 && (
        <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
          {editable
            ? "Aucun fichier. Déposez une capture, une maquette, un compte rendu."
            : "Aucun fichier."}
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
              onRename={editable ? () => setRenamed(file) : undefined}
              onRemove={editable ? () => setDoomed(file) : undefined}
            />
          ))}
        </div>
      )}

      {shown && (
        <AttachmentPreviewDialog
          open
          onOpenChange={(open) => !open && setShown(null)}
          projectId={projectId}
          attachmentId={shown.id}
          filename={shown.filename}
          contentType={shown.content_type}
        />
      )}

      {renamed && (
        <RenameAttachmentDialog
          open
          onOpenChange={(open) => !open && setRenamed(null)}
          filename={renamed.filename}
          onConfirm={(filename) => store.rename(renamed.id, filename)}
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
