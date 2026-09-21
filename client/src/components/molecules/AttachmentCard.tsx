"use client";

import { FileArchive, FileText, FileType, File as FileIcon } from "lucide-react";

import { AttachmentMenu } from "@/components/atoms/AttachmentMenu";
import type { ProjectAttachmentResponse } from "@/lib/api/generated/model";
import { contentUrl, downloadUrl, formatBytes, uploadedBy } from "@/lib/attachments";

interface AttachmentCardProps {
  projectId: number;
  file: ProjectAttachmentResponse;
  /** Shows the file at full size. */
  onOpen: () => void;
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
 * One file of a project, as a card.
 *
 * The image is the original, shown small: at ten megabytes a file and a
 * screen capture for what most of them are, generating a thumbnail would cost
 * a dependency and a second object to keep in step for nothing.
 */
export function AttachmentCard({
  projectId,
  file,
  onOpen,
  onRemove,
}: AttachmentCardProps) {
  return (
    <article className="group flex flex-col rounded-lg border border-slate-300 bg-white shadow-xs transition-shadow hover:border-slate-500 hover:shadow-sm">
      <button
        type="button"
        onClick={onOpen}
        aria-label={`Ouvrir « ${file.filename} »`}
        className="flex h-32 cursor-pointer items-center justify-center overflow-hidden rounded-t-lg border-b border-slate-200 bg-slate-50"
      >
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
      </button>

      <div className="flex min-w-0 items-start gap-1 p-3">
        <div className="min-w-0 flex-1">
          <p
            className="truncate text-sm font-medium text-slate-900"
            title={file.filename}
          >
            {file.filename}
          </p>
          <p className="mt-0.5 text-xs text-slate-500">
            {uploadedBy(file.uploader_name, file.uploaded_at)}
          </p>
          <p className="mt-0.5 text-xs text-slate-400">
            {formatBytes(file.size_bytes)}
          </p>
        </div>

        <AttachmentMenu
          filename={file.filename}
          onOpen={onOpen}
          onDownload={() => {
            window.location.assign(downloadUrl(projectId, file.id));
          }}
          onRemove={onRemove}
        />
      </div>
    </article>
  );
}
