"use client";

import {
  FileArchive,
  FileText,
  FileType,
  File as FileIcon,
  Info,
  Maximize2,
} from "lucide-react";

import { AttachmentMenu } from "@/components/atoms/AttachmentMenu";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { ProjectAttachmentResponse } from "@/lib/api/generated/model";
import { contentUrl, downloadUrl, formatBytes, uploadedBy } from "@/lib/attachments";

interface AttachmentCardProps {
  projectId: number;
  file: ProjectAttachmentResponse;
  /** Shows the file at full size. */
  onOpen: () => void;
  /** Asks to call it something else. What answers is a dialog. Left out
   * where the file may be read and not renamed. */
  onRename?: () => void;
  /** Asks for it to go. What answers is a dialog. Left out where the file
   * may be read and not withdrawn. */
  onRemove?: () => void;
}

/** An icon that says what kind of file it is, when there is no image to show. */
function TypeIcon({ contentType }: { contentType: string }) {
  const className = "size-8 text-slate-400";
  if (contentType === "application/pdf")
    return <FileType className={className} aria-hidden />;
  if (contentType.startsWith("text/"))
    return <FileText className={className} aria-hidden />;
  if (contentType.includes("zip") || contentType.includes("compressed")) {
    return <FileArchive className={className} aria-hidden />;
  }
  return <FileIcon className={className} aria-hidden />;
}

/**
 * The pill every control on the preview is drawn in, so that all read alike.
 *
 * Hidden until the card is reached for: a grid of a dozen files is read as a
 * grid of files, not as a wall of buttons. « Reached for » covers the mouse,
 * the keyboard — a control taking focus shows the lot — and a menu left open
 * while the cursor wanders off.
 */
const OVERLAY =
  "rounded-md bg-white/85 p-1.5 text-slate-600 shadow-xs ring-1 ring-slate-900/5 backdrop-blur-sm transition-all hover:bg-white hover:text-slate-900 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 group-has-[[aria-expanded=true]]:opacity-100";

/**
 * One file of a project, as a card.
 *
 * What one *does* to the file sits on the preview and only shows when the
 * card is reached for: opening at the top left, the rest of the gestures at
 * the top right. What one *reads* stays below and stays put — the name, the
 * weight, and at the end of that line the mark that says who dropped it.
 * Gestures come and go with the cursor; a fact does not.
 *
 * The image is the original, shown small: at ten megabytes a file, and a
 * screen capture for what most of them are, generating a thumbnail would cost
 * a dependency and a second object to keep in step for nothing.
 */
export function AttachmentCard({
  projectId,
  file,
  onOpen,
  onRename,
  onRemove,
}: AttachmentCardProps) {
  const signature = uploadedBy(file.uploader_name, file.uploaded_at);

  return (
    <article className="group flex flex-col rounded-lg border border-slate-300 bg-white shadow-xs transition-shadow hover:border-slate-500 hover:shadow-sm">
      <div className="relative flex h-32 items-center justify-center overflow-hidden rounded-t-lg border-b border-slate-200 bg-slate-50">
        {file.is_image ? (
          /* The file is served by the BFF under whatever type it was dropped
             with; next/image would want to optimise what it cannot know the
             shape of. */
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={contentUrl(projectId, file.id)}
            alt={file.filename}
            loading="lazy"
            className="size-full object-cover"
          />
        ) : (
          <TypeIcon contentType={file.content_type} />
        )}

        <button
          type="button"
          onClick={onOpen}
          aria-label={`Ouvrir « ${file.filename} »`}
          className={`absolute top-2 left-2 cursor-pointer ${OVERLAY}`}
        >
          <Maximize2 className="size-4" aria-hidden />
        </button>

        {/* The menu wears the pill itself rather than sitting in one: two
            roundings on the same button show one inside the other on hover. */}
        <AttachmentMenu
          filename={file.filename}
          onOpen={onOpen}
          onRename={onRename}
          downloadHref={downloadUrl(projectId, file.id)}
          onRemove={onRemove}
          className={`absolute top-2 right-2 ${OVERLAY}`}
        />
      </div>

      <div className="min-w-0 p-3">
        <p
          className="truncate text-sm font-medium text-slate-900"
          title={file.filename}
        >
          {file.filename}
        </p>
        <div className="mt-0.5 flex items-center justify-between gap-2">
          <p className="text-xs text-slate-400">{formatBytes(file.size_bytes)}</p>

          {/* Who dropped it, and when — at the end of the line one reads, and
              always there. It is checked now and then, never read first, so
              it waits behind a mark rather than taking a line of its own. */}
          <Tooltip>
            <TooltipTrigger
              render={
                <span
                  tabIndex={0}
                  aria-label={signature}
                  className="shrink-0 cursor-help text-slate-300 transition-colors hover:text-slate-600"
                />
              }
            >
              <Info className="size-4" aria-hidden />
            </TooltipTrigger>
            {/* Dark, unlike the one the Synthèse uses for a whole table:
                a single line of text reads better lifted off the page than
                sat on another white surface. */}
            <TooltipContent
              side="top"
              align="end"
              className="bg-slate-900 text-white ring-slate-900"
            >
              {signature}
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </article>
  );
}
