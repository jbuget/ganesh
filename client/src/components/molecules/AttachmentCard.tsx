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
  /** Asks to call it something else. What answers is a dialog. */
  onRename: () => void;
  /** Asks for it to go. What answers is a dialog. */
  onRemove: () => void;
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
 * Everything one does to the file sits on the preview itself: opening at the
 * top left, the rest of the gestures at the top right, and who dropped it in
 * the corner one reaches for last. The name below is then left to be read,
 * rather than sharing its line with a signature nobody scans.
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

        {/* Who dropped it, and when — folded away until asked for. It is what
            one checks now and then, never what one reads first. */}
        <Tooltip>
          <TooltipTrigger
            render={
              <span
                tabIndex={0}
                aria-label={signature}
                className={`absolute right-2 bottom-2 cursor-help ${OVERLAY}`}
              />
            }
          >
            <Info className="size-4" aria-hidden />
          </TooltipTrigger>
          <TooltipContent side="top" align="end">
            {signature}
          </TooltipContent>
        </Tooltip>
      </div>

      <div className="min-w-0 p-3">
        <p
          className="truncate text-sm font-medium text-slate-900"
          title={file.filename}
        >
          {file.filename}
        </p>
        <p className="mt-0.5 text-xs text-slate-400">{formatBytes(file.size_bytes)}</p>
      </div>
    </article>
  );
}
