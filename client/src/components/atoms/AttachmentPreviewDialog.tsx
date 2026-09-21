"use client";

import { Download } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { contentUrl, downloadUrl } from "@/lib/attachments";

interface AttachmentPreviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The mission the file belongs to: the address is drawn from the pair. */
  projectId: number;
  attachmentId: number;
  filename: string;
  contentType: string;
}

/**
 * A file at full size, in front of everything else.
 *
 * What can be shown is shown: an image, and a PDF in its own frame. What
 * cannot says so plainly and offers itself for download — a dialog that
 * opened on a blank square would read as a file that failed to load.
 */
export function AttachmentPreviewDialog({
  open,
  onOpenChange,
  projectId,
  attachmentId,
  filename,
  contentType,
}: AttachmentPreviewDialogProps) {
  const isImage = contentType.startsWith("image/");
  const isPdf = contentType === "application/pdf";
  const url = contentUrl(projectId, attachmentId);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle className="min-w-0 truncate">{filename}</DialogTitle>
          {!isImage && !isPdf && (
            <DialogDescription>
              {"Ce type de fichier ne s'affiche pas ici. Téléchargez-le pour l'ouvrir."}
            </DialogDescription>
          )}
        </DialogHeader>

        {isImage && (
          /* The file is served by the BFF under a type the browser decides
             on; next/image would want to optimise what it cannot know the
             shape of. */
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={url}
            alt={filename}
            className="max-h-[70vh] w-full rounded border border-slate-300 object-contain"
          />
        )}

        {isPdf && (
          <iframe
            src={url}
            title={filename}
            className="h-[70vh] w-full rounded border border-slate-300"
          />
        )}

        <div className="flex justify-end">
          {/* A plain link rather than a button: saving a file is what the
              browser does with an address, and it is what keeps the name the
              server put in the header. */}
          <a
            href={downloadUrl(projectId, attachmentId)}
            download={filename}
            className={buttonVariants({
              size: "sm",
              variant: "outline",
              className: "cursor-pointer",
            })}
          >
            <Download className="size-4" aria-hidden />
            Télécharger
          </a>
        </div>
      </DialogContent>
    </Dialog>
  );
}
