"use client";

import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

import { DeleteUpdateDialog } from "@/components/atoms/DeleteUpdateDialog";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { UpdateReactions } from "@/components/atoms/UpdateReactions";
import { MessageComposer } from "@/components/molecules/MessageComposer";
import type { Reaction, UpdateCommentResponse } from "@/lib/api/generated/model";
import { renderMentions, type MentionablePerson } from "@/lib/mentions";
import { since } from "@/lib/relative-dates";

interface UpdateCommentCardProps {
  comment: UpdateCommentResponse;
  now: Date;
  /** The register a mention is read against, as for the update above it. */
  people?: MentionablePerson[];
  onEdit: (body: string) => Promise<void>;
  onRemove: () => Promise<void>;
  onReact: (reaction: Reaction, leaving: boolean) => Promise<void>;
  /** Whether the reader may answer the reply, or only read it. */
  editable?: boolean;
}

/**
 * One reply of a conversation.
 *
 * Lighter than the update it hangs under, and deliberately so: the card of a
 * mise à jour reads as the subject, the replies as what was said about it. No
 * flag for the revue either — one puts a subject on the agenda, not an answer
 * to it.
 *
 * Withdrawn, it keeps its place and its signature: the replies around it keep
 * the order they were written in. Only its text goes.
 */
export function UpdateCommentCard({
  comment,
  now,
  people = [],
  onEdit,
  onRemove,
  onReact,
  editable = true,
}: UpdateCommentCardProps) {
  const [editing, setEditing] = useState(false);
  const [confirmingRemoval, setConfirmingRemoval] = useState(false);

  return (
    <article className="group flex gap-2">
      <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
        {comment.author.initials}
      </span>

      <div className="min-w-0 flex-1">
        <header className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-800">
            {comment.author.display_name}
          </span>
          <span className="text-xs text-slate-400">
            {since(comment.published_at, now)}
            {comment.edited_at && !comment.is_deleted && " · modifiée"}
          </span>

          {/* The author's alone, as above: one answers for one's own words.
              Shown on hover so that a conversation of ten replies does not
              read as a column of icons. */}
          {comment.is_mine && !comment.is_deleted && !editing && (
            <span className="ml-auto flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
              <button
                type="button"
                aria-label="Modifier la réponse"
                onClick={() => setEditing(true)}
                className="cursor-pointer rounded p-1 text-slate-300 transition-colors hover:bg-slate-100 hover:text-slate-600"
              >
                <Pencil className="size-3.5" aria-hidden />
              </button>
              <button
                type="button"
                aria-label="Supprimer la réponse"
                onClick={() => setConfirmingRemoval(true)}
                className="cursor-pointer rounded p-1 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
              >
                <Trash2 className="size-3.5" aria-hidden />
              </button>
            </span>
          )}
        </header>

        {comment.is_deleted ? (
          <p className="text-sm text-slate-400 italic">Message supprimé</p>
        ) : editing ? (
          <MessageComposer
            value={comment.body}
            people={people}
            confirm="Enregistrer"
            onCancel={() => setEditing(false)}
            onConfirm={async (body) => {
              await onEdit(body);
              setEditing(false);
            }}
          />
        ) : (
          <>
            <MarkdownView body={renderMentions(comment.body, people)} />
            <UpdateReactions
              reactions={comment.reactions ?? []}
              editable={editable}
              onToggle={(reaction, leaving) => void onReact(reaction, leaving)}
            />
          </>
        )}
      </div>

      <DeleteUpdateDialog
        open={confirmingRemoval}
        onOpenChange={setConfirmingRemoval}
        reply
        onConfirm={() => {
          setConfirmingRemoval(false);
          return onRemove();
        }}
      />
    </article>
  );
}
