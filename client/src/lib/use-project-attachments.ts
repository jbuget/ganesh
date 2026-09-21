"use client";

import { useCallback, useEffect, useState } from "react";

import type { ProjectAttachmentResponse } from "@/lib/api/generated/model";
import {
  listProjectAttachments,
  removeProjectAttachment,
  uploadProjectAttachment,
} from "@/lib/api/generated/projects/projects";
import { contentUrl } from "@/lib/attachments";

/** What a file weighs at most, as the domain has it. Said here to refuse early. */
export const MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024;

/**
 * The files a project carries.
 *
 * Every write is read back from the server: it decides the order, the size it
 * actually stored and how many updates show each file — none of which the
 * browser could work out on its own.
 */
export function useProjectAttachments(
  projectId: number,
  /**
   * Called after every write. A file dropped from the thread must show up in
   * the Fichiers tab, and one withdrawn there must leave the thread's count.
   */
  onWrite?: () => void | Promise<void>,
) {
  const [files, setFiles] = useState<ProjectAttachmentResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const response = await listProjectAttachments(projectId);
    setFiles(response.data as ProjectAttachmentResponse[]);
  }, [projectId]);

  useEffect(() => {
    let alive = true;
    listProjectAttachments(projectId).then((response) => {
      if (alive) setFiles(response.data as ProjectAttachmentResponse[]);
    });
    return () => {
      alive = false;
    };
  }, [projectId]);

  /**
   * Drops a file and hands back the address it is now served at.
   *
   * The address is what the composer of an update needs: it writes it into
   * the markdown, and the file is a file of the project like any other.
   */
  async function upload(file: File): Promise<string> {
    // Refused here as well as by the domain: sending ten megabytes to be told
    // they were too many is a minute of somebody's morning.
    if (file.size > MAX_ATTACHMENT_BYTES) {
      const refusal = `« ${file.name} » dépasse 10 Mo.`;
      setError(refusal);
      throw new Error(refusal);
    }
    setError(null);
    const response = await uploadProjectAttachment(projectId, { file });
    const stored = response.data as ProjectAttachmentResponse;
    await reload();
    await onWrite?.();
    return contentUrl(projectId, stored.id);
  }

  return {
    files,
    /** What the last drop was refused for, or nothing. */
    error,
    upload,

    async remove(attachmentId: number) {
      await removeProjectAttachment(projectId, attachmentId);
      await reload();
      await onWrite?.();
    },
  };
}
