"use client";

import { Pencil, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { DeleteUpdateDialog } from "@/components/atoms/DeleteUpdateDialog";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { UpdateReactions } from "@/components/atoms/UpdateReactions";
import { Button } from "@/components/ui/button";
import type { Reaction, ProjectUpdateResponse } from "@/lib/api/generated/model";
import { renderMentions, type MentionablePerson } from "@/lib/mentions";
import { since } from "@/lib/relative-dates";

interface ProjectUpdateCardProps {
  update: ProjectUpdateResponse;
  now: Date;
  /**
   * The register, which is what a mention is read against: the name in the
   * text is the one typed that day, and only the register knows who that id
   * is now.
   */
  people?: MentionablePerson[];
  /**
   * Whether this is the update the visit was about — a notification named it.
   * The card then brings itself under the eye and lights up for a moment.
   */
  aimed?: boolean;
  onEdit: (body: string) => Promise<void>;
  onRemove: () => Promise<void>;
  onReact: (reaction: Reaction, leaving: boolean) => Promise<void>;
}

/** How long a thread is given to settle before the reader is left to scroll. */
const SETTLES_IN = 2000;

/**
 * One update from the thread.
 *
 * Withdrawn, it keeps its place and its signature: the thread still tells that
 * something happened, and the replies it drew keep their context. Only its text
 * goes.
 */
export function ProjectUpdateCard({
  update,
  now,
  people = [],
  aimed = false,
  onEdit,
  onRemove,
  onReact,
}: ProjectUpdateCardProps) {
  const [editing, setEditing] = useState(false);
  const [confirmingRemoval, setConfirmingRemoval] = useState(false);
  const card = useRef<HTMLElement>(null);

  // The thread loads after the panel opens, and the update aimed at may be the
  // twentieth down: it brings itself under the eye once it is there.
  //
  // Once is not enough. An image posted above it is measured only when it has
  // loaded, and the card that was centred a frame ago has been pushed off the
  // screen by the time the reader looks. It is therefore followed while the
  // ground under it keeps moving, and let go a moment later — after that the
  // reader is the one scrolling, and being dragged back would be worse than
  // scrolling for oneself.
  useEffect(() => {
    const it = card.current;
    if (!aimed || !it) return;

    const bringItUnderTheEye = () => it.scrollIntoView({ block: "center" });
    bringItUnderTheEye();

    // The thread, not the card: what moves the card is the height of what sits
    // above it.
    const thread = it.parentElement ?? it;
    const watch = new ResizeObserver(bringItUnderTheEye);
    watch.observe(thread);
    const letGo = window.setTimeout(() => watch.disconnect(), SETTLES_IN);

    return () => {
      watch.disconnect();
      window.clearTimeout(letGo);
    };
  }, [aimed]);

  return (
    <article
      ref={card}
      className={`rounded-lg border border-slate-300 bg-white p-3 ${aimed ? "aimed-at" : ""}`}
    >
      <header className="mb-2 flex items-center gap-2">
        <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
          {update.author.initials}
        </span>
        <span className="text-sm font-medium text-slate-800">
          {update.author.display_name}
        </span>
        <span className="text-xs text-slate-400">
          {since(update.published_at, now)}
          {update.edited_at && !update.is_deleted && " · modifiée"}
        </span>

        {update.is_mine && !update.is_deleted && !editing && (
          <span className="ml-auto flex items-center gap-0.5">
            <button
              type="button"
              aria-label="Modifier la mise à jour"
              onClick={() => setEditing(true)}
              className="cursor-pointer rounded p-1 text-slate-300 transition-colors hover:bg-slate-100 hover:text-slate-600"
            >
              <Pencil className="size-3.5" aria-hidden />
            </button>
            <button
              type="button"
              aria-label="Supprimer la mise à jour"
              onClick={() => setConfirmingRemoval(true)}
              className="cursor-pointer rounded p-1 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
            >
              <Trash2 className="size-3.5" aria-hidden />
            </button>
          </span>
        )}
      </header>

      {update.is_deleted ? (
        <p className="text-sm text-slate-400 italic">Message supprimé</p>
      ) : editing ? (
        <Correction
          value={update.body}
          people={people}
          onCancel={() => setEditing(false)}
          onSave={async (body) => {
            await onEdit(body);
            setEditing(false);
          }}
        />
      ) : (
        <>
          <MarkdownView body={renderMentions(update.body, people)} />
          <UpdateReactions
            reactions={update.reactions ?? []}
            onToggle={(reaction, leaving) => void onReact(reaction, leaving)}
          />
        </>
      )}

      <DeleteUpdateDialog
        open={confirmingRemoval}
        onOpenChange={setConfirmingRemoval}
        onConfirm={() => {
          setConfirmingRemoval(false);
          return onRemove();
        }}
      />
    </article>
  );
}

/** Correcting an update, in place in the thread. */
function Correction({
  value,
  people,
  onSave,
  onCancel,
}: {
  value: string;
  people: MentionablePerson[];
  onSave: (body: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [body, setBody] = useState(value);

  return (
    <div className="space-y-2">
      <RichTextEditor
        value={value}
        mentionable={people}
        onChange={setBody}
        onSubmit={() => void onSave(body)}
      />
      <div className="flex items-center gap-2">
        <Button size="sm" disabled={!body.trim()} onClick={() => void onSave(body)}>
          Enregistrer
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>
          Annuler
        </Button>
      </div>
    </div>
  );
}
